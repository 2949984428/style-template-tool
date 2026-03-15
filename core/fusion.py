"""
阶段2：Prompt 融合器
将模板描述 + 用户 prompt 融合为最终生图 prompt
"""

import os
from google.genai import types

import config
from core.utils import get_client, get_logger, FusionError

logger = get_logger("fusion")


def _load_prompt_template():
    path = os.path.join(os.path.dirname(__file__), "..", "prompts", "fusion.txt")
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def fuse_prompt(template_description: str, user_prompt: str, ref_count: int = 1) -> str:
    """
    将模板描述与用户 prompt 融合为 Sandwich Strategy 三层 prompt。

    Args:
        template_description: 风格分析文本（含归因信息）
        user_prompt: 内容意图
        ref_count: 风格参考图的数量，用于 prompt 中标注 Reference Image 1/2/...

    Returns:
        融合后的最终生图 prompt（英文）
    """
    if not template_description.strip():
        raise FusionError("模板描述不能为空")
    if not user_prompt.strip():
        raise FusionError("用户 prompt 不能为空")

    logger.info("融合 prompt (模板 %d 字, 用户 %d 字, 参考图 %d 张)", len(template_description), len(user_prompt), ref_count)
    prompt_template = _load_prompt_template()
    full_prompt = prompt_template.replace(
        "{template_description}", template_description
    ).replace(
        "{user_prompt}", user_prompt
    ).replace(
        "{ref_count}", str(ref_count)
    )

    client = get_client()

    for attempt in range(3):
        response = client.models.generate_content(
            model=config.FUSION_MODEL,
            contents=full_prompt,
            config=types.GenerateContentConfig(temperature=0.5, max_output_tokens=2048),
        )
        result = response.text.strip()
        word_count = len(result.split())

        if word_count >= 150:
            logger.info("融合完成: %d 词 (attempt %d)", word_count, attempt + 1)
            return result

        logger.warning("融合结果过短 (%d 词), 重试 %d/3...", word_count, attempt + 1)

    logger.warning("多次重试后仍较短 (%d 词)，使用最后结果", len(result.split()))
    return result
