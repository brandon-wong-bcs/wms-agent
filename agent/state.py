from typing import NotRequired

from langchain.agents.middleware import AgentMiddleware, AgentState


class WMSState(AgentState):
    """Agent state: the usual messages plus the receipt currently being paged."""

    # NotRequired: a new conversation has no active receipt until a tool sets one.
    active_receipt: NotRequired[dict | None]


class ReceiptStateMiddleware(AgentMiddleware):
    state_schema = WMSState
