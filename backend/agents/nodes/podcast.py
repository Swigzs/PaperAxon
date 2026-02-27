"""播客节点：解读转播客稿 + TTS 生成 MP3。"""
from pathlib import Path

from backend.agents.state import AgentState
from backend.config import PODCASTS_DIR
from backend.db import get_conn
from backend.db import models as db
from backend.services.qwen import generate_podcast_script
from backend.services.tts_aliyun import synthesize_to_file


def run(state: AgentState) -> AgentState:
    if state.get("error"):
        return state
    paper_id = state.get("paper_id")
    interpretation = state.get("interpretation")
    if not paper_id:
        return {**state, "error": "缺少 paper_id"}
    if not interpretation:
        return {**state, "error": "缺少 interpretation，请先完成解读"}

    try:
        script = generate_podcast_script(interpretation)
        PODCASTS_DIR.mkdir(parents=True, exist_ok=True)
        default_path = str(PODCASTS_DIR / f"{paper_id}.mp3")
        audio_path, duration_sec = synthesize_to_file(script, default_path)

        conn = get_conn()
        try:
            db.podcast_upsert(conn, paper_id, audio_path, duration_sec)
        finally:
            conn.close()

        return {**state, "podcast_audio_path": audio_path}
    except Exception as e:
        return {**state, "error": str(e)}
