"""Qwen API（DashScope OpenAI 兼容）用于解读与播客稿。"""
from typing import Optional

from langchain_openai import ChatOpenAI

from backend.config import DASHSCOPE_API_KEY, DASHSCOPE_BASE_URL, QWEN_MODEL


def get_llm(
    model: Optional[str] = None,
    temperature: float = 0.3,
) -> ChatOpenAI:
    return ChatOpenAI(
        model=model or QWEN_MODEL,
        openai_api_key=DASHSCOPE_API_KEY,
        openai_api_base=DASHSCOPE_BASE_URL,
        temperature=temperature,
    )


def generate_interpretation(parse_result: dict) -> str:
    """根据解析结果生成结构化中文解读（Markdown）。"""
    llm = get_llm()
    title = parse_result.get("title", "")
    abstract = parse_result.get("abstract", "")[:4000]
    raw_preview = (parse_result.get("raw_text") or "")[:6000]

    prompt = f"""你是一位学术论文解读助手。请根据以下论文信息，生成一份结构化的中文解读报告（Markdown 格式）。

# 论文标题
{title}

# 摘要
{abstract}

# 正文片段（部分）
{raw_preview}

请按以下结构输出 Markdown，不要省略章节标题：
1. **研究背景与动机**
2. **问题定义与目标**
3. **方法/技术路线概述**
4. **主要结果与实验结论**
5. **创新点与贡献**
6. **局限性与未来工作**
7. **一句话总结**

只输出 Markdown 正文，不要输出代码块标记。"""
    msg = llm.invoke(prompt)
    return msg.content if hasattr(msg, "content") else str(msg)


def generate_podcast_script(interpretation_md: str) -> str:
    """将解读 Markdown 改写成口语化播客稿（分段、可朗读）。"""
    llm = get_llm(temperature=0.5)
    content = interpretation_md[:12000]

    prompt = f"""请将以下论文解读报告改写成适合播客朗读的口语化稿件。要求：
- 开场白：简要介绍「今天要聊的论文是……」
- 分段清晰，每段 2-4 句，便于朗读
- 使用口语化表达，避免生硬书面语
- 结尾有简短收束语
- 总字数控制在 2000 字以内，便于约 15 分钟播客

# 解读报告
{content}

只输出播客稿正文，不要输出代码块或额外说明。"""
    msg = llm.invoke(prompt)
    return msg.content if hasattr(msg, "content") else str(msg)
