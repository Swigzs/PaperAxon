"""TTS：DashScope Qwen TTS，将播客稿转为音频并保存。"""
import wave
from pathlib import Path

import requests

from backend.log_config import get_logger
from backend.config import (
    DASHSCOPE_API_KEY,
    QWEN_TTS_MODEL,
    PODCASTS_DIR,
)

# 非流式 TTS 接口（与百炼 Qwen-TTS API 一致）
DASHSCOPE_TTS_URL = "https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation"
logger = get_logger(__name__)


def synthesize_to_file(text: str, output_path: str | Path) -> tuple[str, float]:
    """
    将文本合成为中文语音并保存为音频文件。
    返回 (实际保存的文件路径, 时长秒)。
    使用 DashScope Qwen TTS（与文本模型共用 DASHSCOPE_API_KEY）。
    若未配置 Key 或调用失败，将文本写入同路径的 .txt，返回 (txt 路径, 0)。
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if not DASHSCOPE_API_KEY:
        _fallback_txt(output_path, text)
        return str(output_path.with_suffix(".txt")), 0.0

    # 百炼 TTS 单次输入长度限制 600（按字符），分段 300 并发送前截断到 600
    segments = _split_text(text, max_chars=300)
    saved_path: Path = output_path
    total_duration = 0.0
    part_paths: list[Path] = []

    for i, seg in enumerate(segments):
        seg = (seg or "").strip()
        if not seg:
            continue
        # 接口限制 600：可能按字节（UTF-8）计，中文约 200 字；按字节截断到 600
        seg_bytes = seg.encode("utf-8")
        if len(seg_bytes) > 600:
            n = 0
            for i in range(len(seg)):
                if len(seg[: i + 1].encode("utf-8")) > 600:
                    break
                n = i + 1
            seg = seg[:n] if n else seg[:200]
        if len(seg.encode("utf-8")) > 600:
            seg = seg[:200]
        try:
            resp = requests.post(
                DASHSCOPE_TTS_URL,
                headers={
                    "Authorization": f"Bearer {DASHSCOPE_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": QWEN_TTS_MODEL,
                    "input": {
                        "text": seg,
                        "voice": "Cherry",
                        "language_type": "Chinese",
                    },
                },
                timeout=60,
            )
            data = resp.json() if resp.content else {}
            out = data.get("output") or {}
            audio_info = out.get("audio") or {}
            url = audio_info.get("url")
            # 成功：HTTP 200 且 body 含 output.audio.url（部分响应无顶层 status_code）
            if resp.status_code != 200 or not url:
                logger.warning("TTS 接口异常 status=%s 或无 url body=%s", resp.status_code, data)
                _fallback_txt(output_path, text)
                return str(output_path.with_suffix(".txt")), 0.0
            r = requests.get(url, timeout=30)
            r.raise_for_status()
            suffix = ".wav" if ".wav" in url.split("?")[0] else ".mp3"
            part_path = output_path.with_suffix(suffix) if len(segments) == 1 else output_path.with_stem(f"{output_path.stem}_part{i}").with_suffix(suffix)
            part_path.write_bytes(r.content)
            saved_path = part_path
            part_paths.append(part_path)
            total_duration += len(r.content) / (16000 * 2) if suffix == ".wav" else len(r.content) / 16000
        except Exception as e:
            logger.warning("TTS 请求异常: %s", e, exc_info=True)
            _fallback_txt(output_path, text)
            return str(output_path.with_suffix(".txt")), 0.0

    # 多段时合并为单个 wav（仅当均为 .wav 且多段时）
    if len(part_paths) > 1 and all(p.suffix.lower() == ".wav" for p in part_paths):
        merged = output_path.with_suffix(".wav")
        try:
            _merge_wav(part_paths, merged)
            for p in part_paths:
                try:
                    p.unlink(missing_ok=True)
                except OSError:
                    pass
            saved_path = merged
        except Exception as e:
            logger.warning("合并 wav 失败，保留最后一段: %s", e)

    return str(saved_path), total_duration if total_duration > 0 else 0.0


def _split_text(text: str, max_chars: int = 300) -> list[str]:
    """按标点分段，每段严格不超过 max_chars（TTS 接口限制 600）。"""
    if not text or not text.strip():
        return []
    text = text.strip()
    if len(text) <= max_chars:
        return [text]
    parts = []
    for sep in "。！？\n":
        text = text.replace(sep, sep + "\x00")
    chunks = [s.strip() for s in text.split("\x00") if s.strip()]
    cur = ""
    for c in chunks:
        if len(c) > max_chars:
            if cur:
                parts.append(cur)
                cur = ""
            for i in range(0, len(c), max_chars):
                parts.append(c[i : i + max_chars])
            continue
        if len(cur) + len(c) + 1 <= max_chars:
            cur = cur + c if not cur else cur + " " + c
        else:
            if cur:
                parts.append(cur)
            cur = c
    if cur:
        parts.append(cur)
    return parts if parts else [text[:max_chars]]


def _merge_wav(part_paths: list[Path], out_path: Path) -> None:
    """将多段 wav 合并为一个（相同参数）。"""
    with wave.open(str(out_path), "wb") as out_wav:
        for i, p in enumerate(part_paths):
            with wave.open(str(p), "rb") as inc:
                if i == 0:
                    out_wav.setnchannels(inc.getnchannels())
                    out_wav.setsampwidth(inc.getsampwidth())
                    out_wav.setframerate(inc.getframerate())
                out_wav.writeframes(inc.readframes(inc.getnframes()))


def _fallback_txt(output_path: Path, text: str) -> None:
    txt_path = output_path.with_suffix(".txt")
    txt_path.write_text(text, encoding="utf-8")


