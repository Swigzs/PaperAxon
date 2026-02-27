"""规划节点：规则路由，根据 request_type 与 state 返回 next_node。"""
from backend.agents.state import AgentState

# 节点名常量
END = "__end__"


def route(state: AgentState) -> AgentState:
    request_type = state.get("request_type") or "interpret"
    next_node = END

    if state.get("error"):
        return {**state, "next_node": END}

    if request_type == "related_only":
        next_node = "retriever"
        return {**state, "next_node": next_node}

    if request_type == "podcast_only":
        if state.get("interpretation") and state.get("paper_id"):
            next_node = "podcast"
        return {**state, "next_node": next_node}

    # interpret / full_pipeline
    if not state.get("parse_result") and (state.get("paper_input") or state.get("paper_id")):
        next_node = "parser"
    elif state.get("parse_result") and not state.get("interpretation"):
        next_node = "interpreter"
    elif state.get("interpretation") and not state.get("memory_updated"):
        next_node = "memory"
    elif state.get("memory_updated") and state.get("paper_id"):
        next_node = "podcast"
    else:
        next_node = END

    return {**state, "next_node": next_node}
