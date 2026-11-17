import streamlit as st
from groq import APIError
from agent.runner import stream_turn, load_receipt_page, receipt_state
import uuid

if "active_receipt" not in st.session_state:
    st.session_state.active_receipt = None

if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())

# Receipt line pages the user loaded with the button (display only)
if "extra_pages" not in st.session_state:
    st.session_state.extra_pages = []

if "page_error" not in st.session_state:
    st.session_state.page_error = None


def load_next_page():
    """Button callback: fetch the next receipt page without the LLM."""
    ar = st.session_state.active_receipt
    try:
        result = load_receipt_page(
            st.session_state.thread_id, ar["receiptNo"], ar["nextSkipCount"]
        )
    except Exception as exc:
        print("Load more failed:", type(exc).__name__, exc, flush=True)
        st.session_state.page_error = "Could not load the next lines. See the terminal for details."
        return
    state = receipt_state(result)
    if state is None:
        st.session_state.page_error = result.get("error", "Could not load the next lines.")
        return
    st.session_state.page_error = None
    st.session_state.extra_pages.append(result["items"])
    st.session_state.active_receipt = state

st.title("Warehouse AI Assistant")

# Conversation history
if "messages" not in st.session_state:
    st.session_state.messages = []

if "reasoning" not in st.session_state:
    st.session_state.reasoning = []

# Display previous messages
assistant_index = 0
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message["role"] == "assistant":
            reasoning = (
                st.session_state.reasoning[assistant_index]
                if assistant_index < len(st.session_state.reasoning)
                else ""
            )
            if reasoning:
                with st.expander("Reasoning", expanded=False):
                    st.markdown(reasoning)
            assistant_index += 1


prompt = st.chat_input("Ask me about the warehouse...")


if prompt:

    # Pages loaded by the button belong to the previous question; clear them
    st.session_state.extra_pages = []
    st.session_state.page_error = None

    # Save user message
    st.session_state.messages.append({
        "role": "user",
        "content": prompt
    })

    # Display user message
    with st.chat_message("user"):
        st.markdown(prompt)


    # Assistant
    with st.chat_message("assistant"):

        with st.expander("Reasoning", expanded=False):
            reasoning_placeholder = st.empty()

        response_placeholder = st.empty()

        full_reasoning = ""
        full_response = ""

        try:
            for kind, payload in stream_turn(
                st.session_state.thread_id,
                prompt,
                st.session_state.active_receipt,
            ):
                if kind == "receipt_state":
                    previous = st.session_state.active_receipt
                    if not previous or previous["receiptNo"] != payload["receiptNo"]:
                        st.session_state.extra_pages = []
                    st.session_state.page_error = None
                    st.session_state.active_receipt = payload
                elif kind == "reasoning":
                    full_reasoning += payload
                    reasoning_placeholder.markdown(full_reasoning)
                elif kind == "answer":
                    full_response += payload
                    response_placeholder.markdown(full_response + "▌")
        except APIError as exc:
            print("Groq error details:", exc.body, flush=True)
            response_placeholder.empty()
            reasoning_placeholder.empty()
            st.error("The model couldn't complete its request. See the terminal for error details.")
            st.stop()

        # Final render without cursor
        response_placeholder.markdown(full_response)
        if not full_reasoning:
            reasoning_placeholder.markdown("No reasoning content was returned.")


    # Store assistant message in conversation history
    st.session_state.messages.append({
        "role": "assistant",
        "content": full_response
    })
    st.session_state.reasoning.append(full_reasoning)


# Receipt paging panel: pages loaded by the button, and the button itself
for page in st.session_state.extra_pages:
    st.dataframe(page, use_container_width=True)

ar = st.session_state.active_receipt
if ar and ar["hasMore"]:
    st.button(
        f"Load more lines ({ar['nextSkipCount']} of {ar['totalCount']} loaded)",
        on_click=load_next_page,
    )
if st.session_state.page_error:
    st.error(st.session_state.page_error)
