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


def fuse_prompt(template_description: str, user_prompt: str) -> str:
    """
    将模板描述与用户 prompt 融合。

    Returns:
        融合后的最终生图 prompt（英文）
    """
    if not template_description.strip():
        raise FusionError("模板描述不能为空")
    if not user_prompt.strip():
        raise FusionError("用户 prompt 不能为空")

    logger.info("融合 prompt (模板 %d 字, 用户 %d 字)", len(template_description), len(user_prompt))
    prompt_template = _load_prompt_template()
    full_prompt = prompt_template.replace(
        "{template_description}", template_description
    ).replace(
        "{user_prompt}", user_prompt
    )

    client = get_client()
    response = client.models.generate_content(
        model=config.FUSION_MODEL,
        contents=full_prompt,
        config=types.GenerateContentConfig(temperature=0.4, max_output_tokens=1024),
    )

    return response.text.strip()
