from typing import NotRequired
import json
from langgraph.types import Command
from langchain_core.messages import HumanMessage, SystemMessage

from langchain.agents.middleware import AgentMiddleware, AgentState


class WMSState(AgentState):
    """Agent state: the usual messages plus the receipt currently being paged."""

    # NotRequired: a new conversation has no active receipt until a tool sets one.
    active_receipt: NotRequired[dict | None]


class ReceiptStateMiddleware(AgentMiddleware):
    state_schema = WMSState

    def wrap_tool_call(self, request, handler):
        result = handler(request)
        if request.tool_call["name"] != "get_receipt_detail":
            return result

        data = json.loads(result.content)
        if "error" in data:
            return result

        return Command(update={
            "messages": [result],
            "active_receipt": {
                "receiptNo": data["receiptNo"],
                "totalCount": data["totalCount"],
                "hasMore": data["hasMore"],
                "nextSkipCount": data["nextSkipCount"],
            },
        })

    def wrap_model_call(self, request, handler):
        ar = request.state.get("active_receipt")
        if ar:
            context = (
                f"[context: activeReceipt receiptNo={ar['receiptNo']}, "
                f"totalCount={ar['totalCount']}, hasMore={ar['hasMore']}, "
                f"nextSkipCount={ar['nextSkipCount']}]"
            )
            base = request.system_message.content if request.system_message else ""
            request = request.override(
                system_message=SystemMessage(content=f"{base}\n\n{context}")
            )
        return handler(request)