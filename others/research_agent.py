"""
Research Agent POC  (Groq LLM + Tavily search, no agent framework)

Run (PowerShell):
    py -m pip install groq httpx beautifulsoup4
    $env:GROQ_API_KEY="..."
    $env:TAVILY_API_KEY="..."
    py research_agent.py "Rust vs Go for backend development"
"""
import inspect, json, os, re, sys
import httpx
from bs4 import BeautifulSoup
from groq import Groq, APIStatusError, NotFoundError, AuthenticationError, PermissionDeniedError

MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")  # must support tool calling
MAX_STEPS = 20          # guardrail: hard stop on the loop
MIN_SEARCHES = 3        # done rule
MIN_SOURCES = 3         # done rule
PAGE_CHAR_LIMIT = 2500  # guardrail: truncate pages before the LLM sees them
SNIPPET_CHAR_LIMIT = 250
KEEP_FULL_RESULTS = 2   # only the newest N tool results stay full-size in the history

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))


# ---------------------------------------------------------------- 3. STATE
# "Done" is measured against this object, not against the LLM's feelings.
def new_state():
    return {
        "topic": "", "search_count": 0, "sources": {},   # url -> title
        "notes": [], "fetched": set(), "queries": set(),  # auto-memory + what was already searched/read
        "summary": "", "findings": [], "pros": [], "cons": [], "recommendation": "",
    }


# ---------------------------------------------------------------- 1. TOOLS (plain functions)
def search_web(state, query: str) -> str:
    key = re.sub(r"\W+", " ", query.lower()).strip()
    if key in state["queries"]:
        return "You already ran this exact search. Fetch a page from your earlier results or submit."
    state["queries"].add(key)
    state["search_count"] += 1
    r = httpx.post(
        "https://api.tavily.com/search",
        headers={"Authorization": f"Bearer {os.environ.get('TAVILY_API_KEY')}"},
        json={"query": query, "max_results": 4},
        timeout=20,
    )
    r.raise_for_status()
    out, titles = [], []
    for item in r.json().get("results", []):
        state["sources"][item["url"]] = item["title"]
        out.append(f"- {item['title']}\n  {item['url']}\n  {item['content'][:SNIPPET_CHAR_LIMIT]}")
        titles.append(f"{item['title'][:60]} ({item['url']})")
    if titles:  # AUTO-MEMORY: the script remembers what was found, not the LLM
        state["notes"].append(f"Search '{query}' found: " + "; ".join(titles))
    return "\n".join(out) or "No results."


def get_page(state, url: str) -> str:
    if url in state["fetched"]:
        return "You already fetched this page. Use your saved notes, or fetch a DIFFERENT url."
    state["fetched"].add(url)
    r = httpx.get(url, timeout=15, follow_redirects=True,
                  headers={"User-Agent": "Mozilla/5.0 research-agent-poc"})
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header"]):
        tag.decompose()
    text = re.sub(r"\s+", " ", soup.get_text(" ")).strip()
    state["sources"].setdefault(url, soup.title.string if soup.title else url)
    digest = digest_page(url, text[:PAGE_CHAR_LIMIT], state["topic"])
    state["notes"].append(f"Page {url}: {digest}")  # AUTO-MEMORY
    return digest


def digest_page(url: str, text: str, topic: str) -> str:
    """Separate small LLM call: raw page -> a few key facts. History never holds raw pages."""
    prompt = (f"Topic being researched: {topic}\nPage: {url}\n\nExtract the 4-6 most relevant concrete "
              f"facts from this page text as short bullet points (max 600 characters total). "
              f"Facts only, no intro.\n\n{text}")
    try:
        out = client.chat.completions.create(
            model=MODEL, messages=[{"role": "user", "content": prompt}]).choices[0].message.content
        return (out or "").strip()[:700] or text[:500]
    except Exception:
        return text[:500]  # fallback so a failed digest never breaks the run


# ---- the done check lives here
def missing_requirements(state) -> list[str]:
    missing = []
    if state["search_count"] < MIN_SEARCHES:
        missing.append(f"at least {MIN_SEARCHES} searches (done: {state['search_count']})")
    if len(state["sources"]) < MIN_SOURCES:
        missing.append(f"at least {MIN_SOURCES} sources (have: {len(state['sources'])})")
    for field in ("summary", "recommendation"):
        if not state[field]:
            missing.append(field)
    for field in ("findings", "pros", "cons"):
        if not state[field]:
            missing.append(field)
    return missing


def submit_findings(state, summary: str, findings: list, pros: list,
                    cons: list, recommendation: str) -> str:
    state.update(summary=summary, findings=findings, pros=pros,
                 cons=cons, recommendation=recommendation)
    missing = missing_requirements(state)
    if missing:  # push back: the agent is NOT done
        return "REJECTED. Not done yet. Missing: " + "; ".join(missing) + ". Keep researching."
    return "ACCEPTED"


# ---------------------------------------------------------------- 2. TOOL DESCRIPTIONS (for the LLM)
def tool_spec(name, desc, props, required):
    return {"type": "function", "function": {
        "name": name, "description": desc,
        "parameters": {"type": "object", "properties": props, "required": required}}}

TOOLS = [
    tool_spec("search_web", "Search the web. Returns titles, URLs and snippets.",
              {"query": {"type": "string"}}, ["query"]),
    tool_spec("get_page", "Fetch the text of a web page by URL.",
              {"url": {"type": "string"}}, ["url"]),
    tool_spec("submit_findings",
              "Call when you believe research is complete. Will be rejected if requirements are missing.",
              {"summary": {"type": "string"},
               "findings": {"type": "array", "items": {"type": "string"}},
               "pros": {"type": "array", "items": {"type": "string"}},
               "cons": {"type": "array", "items": {"type": "string"}},
               "recommendation": {"type": "string"}},
              ["summary", "findings", "pros", "cons", "recommendation"]),
]
REGISTRY = {"search_web": search_web, "get_page": get_page, "submit_findings": submit_findings}


def call_tool(name, state, args):
    """Ignore unexpected extra arguments the LLM invents (e.g. save_note(source=...))."""
    fn = REGISTRY[name]
    allowed = set(inspect.signature(fn).parameters) - {"state"}
    return fn(state, **{k: v for k, v in args.items() if k in allowed})

SYSTEM = f"""You are a research agent. Research the user's topic using the tools.
Rules:
- Do at least {MIN_SEARCHES} different searches and use at least {MIN_SOURCES} sources.
- Use get_page when a snippet is not enough detail. Never fetch the same URL twice.
- Search results and fetched pages are automatically summarised and remembered for you (see saved notes).
- Do not repeat searches. Fetch a promising URL from earlier results instead.
- You have a limited number of steps. Do not research forever: once you have enough, call submit_findings.
- Only when finished, call submit_findings. If it is REJECTED, continue researching.
- Base claims on what the tools returned; do not invent facts."""


# ---------------------------------------------------------------- 4. THE LOOP
def notes_text(state, cap=5000):
    text = "\n".join(f"- {n}" for n in state["notes"]) or "(none yet)"
    return text if len(text) <= cap else "...(older notes cut)\n" + text[-cap:]



def compact(messages, keep_full=KEEP_FULL_RESULTS, short=300):
    """Shrink old tool results so the conversation stays small (context management).
    The agent has already 'read' them; what matters is kept in its own notes/messages."""
    tool_idx = [i for i, m in enumerate(messages) if m["role"] == "tool"]
    for i in tool_idx[:-keep_full] if keep_full else tool_idx:
        c = messages[i]["content"]
        if len(c) > short:
            messages[i]["content"] = c[:short] + " ...[older result truncated]"



def run_agent(topic: str) -> dict:
    state = new_state()
    state["topic"] = topic
    messages = [{"role": "system", "content": SYSTEM},
                {"role": "user", "content": f"Research this topic: {topic}"}]
    accepted = False

    for step in range(1, MAX_STEPS + 1):
        compact(messages)  # keep history small every step, not only after an error
        steps_left = MAX_STEPS - step + 1
        force_submit = steps_left <= 3   # last 3 steps: the agent MUST wrap up
        status = (f"[STATUS] Step {step}/{MAX_STEPS}. Searches: {state['search_count']}/{MIN_SEARCHES}, "
                  f"sources: {len(state['sources'])}/{MIN_SOURCES}.\n"
                  "Your notes so far:\n" + notes_text(state))
        if state["search_count"] >= MIN_SEARCHES and len(state["sources"]) >= MIN_SOURCES:
            status += "\nMinimums met. Read at most 1-2 more pages, then call submit_findings."
        if force_submit:
            status += "\nFINAL STEPS: call submit_findings NOW using your notes."
        choice = ({"type": "function", "function": {"name": "submit_findings"}}
                  if force_submit else "auto")
        try:
            # status is added to this call only (not stored), so the history doesn't grow
            resp = client.chat.completions.create(
                model=MODEL, messages=messages + [{"role": "user", "content": status}],
                tools=TOOLS, tool_choice=choice)
        except APIStatusError as e:
            if e.status_code == 413:  # request too big: retrying the SAME request is pointless
                print(f"[step {step}] request too large -> shrinking history. Details: {str(e)[:300]}")
                compact(messages)
                if step > 1 and all(len(m.get("content") or "") < 400 for m in messages if m["role"] == "tool"):
                    compact(messages, keep_full=0, short=150)  # last resort
                continue
            if e.status_code in (401, 403, 404):
                sys.exit(f"Fatal Groq error (check GROQ_API_KEY / GROQ_MODEL={MODEL}): {e}")
            print(f"[step {step}] API error {e.status_code}, retrying: {str(e)[:200]}")
            continue
        except (NotFoundError, AuthenticationError, PermissionDeniedError) as e:
            # config problems (bad model name / bad key) never fix themselves: stop now
            sys.exit(f"Fatal Groq error (check GROQ_API_KEY / GROQ_MODEL): {e}")
        except Exception as e:  # e.g. malformed tool call from the model -> nudge and retry
            print(f"[step {step}] LLM error, retrying: {str(e)[:120]}")
            messages.append({"role": "user", "content": "Your last tool call was malformed. Try again."})
            continue

        msg = resp.choices[0].message
        if not msg.tool_calls:  # LLM answered in plain text instead of calling a tool
            print(f"[step {step}] (no tool call) {(msg.content or '')[:80]!r}")
            messages.append({"role": "assistant", "content": msg.content or ""})
            messages.append({"role": "user",
                             "content": "Continue using tools, then call submit_findings when done."})
            continue

        messages.append({"role": "assistant", "content": msg.content or "",
                         "tool_calls": [{"id": c.id, "type": "function",
                                         "function": {"name": c.function.name,
                                                      "arguments": c.function.arguments}}
                                        for c in msg.tool_calls]})
        for call in msg.tool_calls:
            name = call.function.name
            try:
                args = json.loads(call.function.arguments or "{}")
                print(f"[step {step}] {name}({json.dumps(args)[:90]})")
                result = call_tool(name, state, args)
            except Exception as e:  # tool errors go back to the LLM as observations
                result = f"Tool error: {e}"
            print(f"           -> {str(result)[:90]!r}")
            messages.append({"role": "tool", "tool_call_id": call.id, "content": str(result)})
            if name == "submit_findings" and result == "ACCEPTED":
                accepted = True
        if accepted:  # 5. DONE CHECK passed
            print(f"[step {step}] done check passed")
            break
    else:
        print(f"Hit MAX_STEPS={MAX_STEPS}; writing report with what we have.")
    return state


# ---------------------------------------------------------------- 6. REPORT WRITER
def write_report(state) -> str:
    sources = "\n".join(f"- [{t}]({u})" for u, t in state["sources"].items())
    prompt = ("Write a clear markdown report with sections: Executive Summary, Key Findings, "
              "Pros, Cons, Recommendation. Use ONLY this data. Do not add a Sources section.\n\n"
              + json.dumps({k: state[k] for k in
                            ("topic", "summary", "findings", "pros", "cons", "recommendation")}))
    body = client.chat.completions.create(
        model=MODEL, messages=[{"role": "user", "content": prompt}]).choices[0].message.content
    return f"# Research Report: {state['topic']}\n\n{body}\n\n## Sources\n{sources}\n"


if __name__ == "__main__":
    topic = " ".join(sys.argv[1:]) or input("Research topic: ")
    state = run_agent(topic)
    missing = missing_requirements(state)
    if not state["summary"]:
        sys.exit("The agent never submitted findings, so no report was written. "
                 "See the messages above (try GROQ_MODEL=openai/gpt-oss-120b).")
    report = write_report(state)
    if missing:
        report += f"\n> Note: incomplete research. Missing: {'; '.join(missing)}\n"
    with open("report.md", "w", encoding="utf-8") as f:
        f.write(report)
    print("Saved report.md")
