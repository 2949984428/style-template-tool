"""
阶段2：Prompt 融合器
将模板描述 + 用户 prompt 融合为最终生图 prompt
"""

import os
from google import genai
from google.genai import types

import config


def _load_prompt_template():
    """读取融合 prompt 模板"""
    prompt_path = os.path.join(os.path.dirname(__file__), "..", "prompts", "fusion.txt")
    with open(prompt_path, "r", encoding="utf-8") as f:
        return f.read()


def fuse_prompt(template_description: str, user_prompt: str) -> str:
    """
    将模板描述与用户 prompt 融合

    Args:
        template_description: 阶段1生成的模板描述
        user_prompt: 用户输入的内容意图

    Returns:
        融合后的最终生图 prompt（英文）
    """
    if not template_description.strip():
        raise ValueError("模板描述不能为空")

    if not user_prompt.strip():
        raise ValueError("用户 prompt 不能为空")

    # 加载 prompt 模板并填入变量
    prompt_template = _load_prompt_template()
    full_prompt = prompt_template.replace(
        "{template_description}", template_description
    ).replace(
        "{user_prompt}", user_prompt
    )

    # 调用 Gemini 文本模型
    client = genai.Client(api_key=config.GEMINI_API_KEY)

    response = client.models.generate_content(
        model=config.FUSION_MODEL,
        contents=full_prompt,
        config=types.GenerateContentConfig(
            temperature=0.4,
            max_output_tokens=1024,
        ),
    )

    return response.text.strip()
