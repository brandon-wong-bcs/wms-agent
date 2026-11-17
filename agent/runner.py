"""Run one conversation turn against the agent, with no UI dependencies.

stream_turn() is a generator that yields (kind, payload) events:

    ("reasoning", str)        a chunk of the model's reasoning text
    ("answer", str)           a chunk of the model's answer text
    ("receipt_state", dict)   paging state from a successful get_receipt_detail

load_receipt_page() fetches a receipt page without the LLM (for a UI button).

Callers (Streamlit, a CLI, tests) decide how to display or store them.
APIError from the model provider is not caught here; callers handle it.
"""

import json
import datetime
from pathlib import Path

from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.messages import AIMessageChunk, HumanMessage, ToolMessage

from agent.wms_agent import agent
from tools.receipt import get_receipt_detail


TOKEN_LOG = Path(__file__).resolve().parents[1] / "logs" / "tokens.jsonl"


class TokenLogger(BaseCallbackHandler):
    """Print token usage per LLM call and append it to logs/tokens.jsonl."""

    def __init__(self, thread_id=None):
        self.thread_id = thread_id

    def on_llm_end(self, response, **kwargs):
        for generations in response.generations:
            for gen in generations:
                usage = getattr(getattr(gen, "message", None), "usage_metadata", None)
                if not usage:
                    continue
                input_tok = usage.get("input_tokens")
                output_tok = usage.get("output_tokens")
                print(f"[LLM call] input={input_tok} output={output_tok}")
                self._write({
                    "time": datetime.datetime.now().isoformat(timespec="seconds"),
                    "thread_id": self.thread_id,
                    "input": input_tok,
                    "output": output_tok,
                    "total": usage.get("total_tokens"),
                })

    def _write(self, record):
        # Logging must never break a chat turn.
        try:
            TOKEN_LOG.parent.mkdir(exist_ok=True)
            with open(TOKEN_LOG, "a", encoding="utf-8") as f:
                f.write(json.dumps(record) + "\n")
        except OSError as exc:
            print(f"[token log failed: {exc}]")


def _with_receipt_context(text, active_receipt):
    """Append the activeReceipt context line (replaced by agent state in step 1.4)."""
    if not active_receipt:
        return text
    return text + (
        f"\n\n[context: activeReceipt receiptNo={active_receipt['receiptNo']}, "
        f"totalCount={active_receipt['totalCount']}, hasMore={active_receipt['hasMore']}, "
        f"nextSkipCount={active_receipt['nextSkipCount']}]"
    )


def receipt_state(result):
    """Return paging state from a successful get_receipt_detail result, else None."""
    if not isinstance(result, dict) or "error" in result:
        return None
    return {
        "receiptNo": result["receiptNo"],
        "totalCount": result["totalCount"],
        "hasMore": result["hasMore"],
        "nextSkipCount": result["nextSkipCount"],
    }


def _receipt_state_from(message):
    """Parse a get_receipt_detail ToolMessage into paging state, else None."""
    try:
        return receipt_state(json.loads(message.content))
    except (TypeError, ValueError, KeyError):
        return None


def load_receipt_page(thread_id, receipt_no, skip_count):
    """Fetch one page of receipt lines directly (no LLM call) for a UI button.

    The lines go to the caller for display. The thread only gets a short note
    saying the user viewed them, so the model knows what was seen without
    carrying the data; it can call get_receipt_detail itself if it needs them.
    Returns the tool result (which may be {"error": ...}).
    """
    result = get_receipt_detail.invoke(
        {"receiptNo": receipt_no, "skipCount": skip_count}
    )
    state = receipt_state(result)
    if state is None:
        return result

    first = skip_count + 1
    last = skip_count + len(result["items"])
    note = (
        f"[ui-note: the user loaded lines {first}-{last} of receipt "
        f"{receipt_no} with the Load more button (totalCount="
        f"{state['totalCount']}, hasMore={state['hasMore']}, "
        f"nextSkipCount={state['nextSkipCount']}). Those lines were shown to "
        f"the user, not to you. Call get_receipt_detail with skipCount="
        f"{skip_count} only if you need their data.]"
    )
    agent.update_state(
        {"configurable": {"thread_id": thread_id}},
        {"messages": [HumanMessage(content=note)]},
    )
    return result


def stream_turn(thread_id, text, active_receipt=None):
    """Send one user message on a thread and yield events as the agent responds."""
    # The checkpointer already holds earlier turns; send only the new message.
    user_message = {
        "role": "user",
        "content": _with_receipt_context(text, active_receipt),
    }

    for message, _metadata in agent.stream(
        {"messages": [user_message]},
        {
            "callbacks": [TokenLogger(thread_id)],
            "configurable": {"thread_id": thread_id},
        },
        stream_mode="messages",
    ):
        if isinstance(message, ToolMessage) and message.name == "get_receipt_detail":
            state = _receipt_state_from(message)
            if state:
                yield ("receipt_state", state)

        # Tool results are not displayed; only text generated by the model is.
        if isinstance(message, AIMessageChunk):
            reasoning = message.additional_kwargs.get("reasoning_content")
            if isinstance(reasoning, str):
                yield ("reasoning", reasoning)
            if isinstance(message.content, str):
                yield ("answer", message.content)
