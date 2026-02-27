"""解读节点：调用 Qwen 生成中文解读 Markdown。"""
from backend.agents.state import AgentState
from backend.services.qwen import generate_interpretation


def run(state: AgentState) -> AgentState:
    if state.get("error"):
        return state
    parse_result = state.get("parse_result")
    if not parse_result:
        return {**state, "error": "缺少 parse_result"}
    try:
        interpretation = generate_interpretation(parse_result)
        return {**state, "interpretation": interpretation}
    except Exception as e:
        return {**state, "error": str(e)}
