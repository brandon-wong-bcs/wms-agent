"""Chat with the WMS agent in the terminal, without Streamlit.

Run from the project root:
    python -m helpers.chat_cli

Type a question and press Enter. Type "exit" (or press Ctrl+C) to quit.
"""

import uuid

from groq import APIError

# stream_turn is the same function the Streamlit app uses.
# Importing it also loads the agent, the tools, and your .env settings.
from agent.runner import stream_turn


def main():
    # One thread id for the whole session. The agent's checkpointer uses it to
    # remember earlier turns, so follow-up questions work.
    thread_id = str(uuid.uuid4())

    # Paging state from get_receipt_detail. In the Streamlit app this lives in
    # st.session_state; here it is just a variable.
    active_receipt = None

    print("Warehouse assistant. Type 'exit' to quit.\n")

    while True:
        # Read one line from the user. Ctrl+C or Ctrl+D ends the program.
        try:
            line = input("> ").strip()
        except (KeyboardInterrupt, EOFError):
            print()
            break

        if line.lower() in ("exit", "quit"):
            break
        if not line:
            continue  # ignore empty input

        try:
            # stream_turn yields (kind, payload) events as the agent works.
            for kind, payload in stream_turn(thread_id, line, active_receipt):
                if kind == "answer":
                    # end="" keeps the text on one line, flush=True shows each
                    # chunk immediately so the answer appears to stream.
                    print(payload, end="", flush=True)
                elif kind == "receipt_state":
                    # Remember paging info so the next turn can use it.
                    active_receipt = payload
                # "reasoning" events are ignored here; only the answer is shown.
        except APIError as exc:
            # The runner does not catch model errors, so we do it here.
            print(f"\n[model error: {exc}]")

        print("\n")  # blank line between turns


if __name__ == "__main__":
    main()
