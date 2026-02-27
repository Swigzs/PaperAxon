"""LangGraph 图：规划 + 解析/解读/检索/记忆/播客。"""
from typing import Any, Literal

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from backend.agents.state import AgentState
from backend.agents.nodes.planner import route as planner_route
from backend.agents.nodes.parser import run as parser_run
from backend.agents.nodes.interpreter import run as interpreter_run
from backend.agents.nodes.retriever import run as retriever_run
from backend.agents.nodes.memory import run as memory_run
from backend.agents.nodes.podcast import run as podcast_run


def _route_after_planner(state: AgentState) -> Literal["parser", "interpreter", "retriever", "memory", "podcast", "__end__"]:
    n = (state.get("next_node") or "__end__").strip()
    if n == "parser":
        return "parser"
    if n == "interpreter":
        return "interpreter"
    if n == "retriever":
        return "retriever"
    if n == "memory":
        return "memory"
    if n == "podcast":
        return "podcast"
    return "__end__"


def create_graph():
    graph = StateGraph(AgentState)

    graph.add_node("planner", planner_route)
    graph.add_node("parser", parser_run)
    graph.add_node("interpreter", interpreter_run)
    graph.add_node("retriever", retriever_run)
    graph.add_node("memory", memory_run)
    graph.add_node("podcast", podcast_run)

    graph.set_entry_point("planner")
    graph.add_conditional_edges("planner", _route_after_planner)
    graph.add_edge("parser", "planner")
    graph.add_edge("interpreter", "planner")
    graph.add_edge("retriever", END)
    graph.add_edge("memory", "planner")
    graph.add_edge("podcast", END)

    memory = MemorySaver()
    return graph.compile(checkpointer=memory)


def run_interpret(paper_id: str, paper_input: dict) -> dict[str, Any]:
    """运行解读流水线：parser -> interpreter -> memory -> podcast。"""
    app = create_graph()
    initial: AgentState = {
        "request_type": "interpret",
        "paper_id": paper_id,
        "paper_input": paper_input,
    }
    config = {"configurable": {"thread_id": f"interpret-{paper_id}"}}
    final = None
    for event in app.stream(initial, config):
        for v in event.values():
            final = v
    return final or initial


def run_podcast_only(paper_id: str, interpretation: str) -> dict[str, Any]:
    """仅生成播客（已有解读）。"""
    app = create_graph()
    initial: AgentState = {
        "request_type": "podcast_only",
        "paper_id": paper_id,
        "interpretation": interpretation,
    }
    config = {"configurable": {"thread_id": f"podcast-{paper_id}"}}
    final = None
    for event in app.stream(initial, config):
        for v in event.values():
            final = v
    return final or initial
