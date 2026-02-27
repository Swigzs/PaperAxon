"""LangGraph 状态定义。"""
from typing import Any, Optional, TypedDict


class AgentState(TypedDict, total=False):
    request_type: str  # interpret | related_only | podcast_only | full_pipeline
    paper_input: dict  # path 或 arxiv_id
    paper_id: str
    parse_result: dict
    interpretation: str
    related_papers: list
    memory_updated: bool
    podcast_audio_path: str
    error: Optional[str]
    next_node: str  # planner 输出
