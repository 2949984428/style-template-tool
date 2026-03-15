"""
阶段1：图集分析器 V2
输入风格图集，调用 Gemini 多模态分析，输出结构化模板描述 + 代表图编号 + 图像类型判断
"""

import os
import re
import json
import base64
from PIL import Image
from io import BytesIO
from google import genai
from google.genai import types

import config


def _load_prompt():
    """读取分析 prompt 模板"""
    prompt_path = os.path.join(os.path.dirname(__file__), "..", "prompts", "analyze_v2.txt")
    with open(prompt_path, "r", encoding="utf-8") as f:
        return f.read()


def _image_to_part(image_path: str) -> types.Part:
    """将图片文件转换为 Gemini API 的 Part 对象"""
    with open(image_path, "rb") as f:
        data = f.read()

    # 检测 MIME 类型
    ext = os.path.splitext(image_path)[1].lower()
    mime_map = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".webp": "image/webp",
        ".gif": "image/gif",
    }
    mime_type = mime_map.get(ext, "image/jpeg")

    return types.Part.from_bytes(data=data, mime_type=mime_type)


def _parse_representative_images(text: str) -> list[int]:
    """从响应文本中解析代表图编号"""
    match = re.search(r"REPRESENTATIVE_IMAGES:\s*\[([^\]]+)\]", text)
    if match:
        nums = re.findall(r"\d+", match.group(1))
        return [int(n) for n in nums]
    return [1]  # 默认选第一张


def _parse_json_fields(text: str) -> dict:
    """从响应文本中解析JSON字段"""
    # 尝试提取JSON代码块
    json_match = re.search(r'```json\s*\n(.*?)\n```', text, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(1))
        except json.JSONDecodeError:
            pass
    
    # 尝试直接提取JSON对象
    json_match = re.search(r'\{[\s\S]*?"has_subject"[\s\S]*?\}', text)
    if json_match:
        try:
            return json.loads(json_match.group(0))
        except json.JSONDecodeError:
            pass
    
    # 默认值
    return {
        "has_subject": True,
        "image_type": "product",
        "subject_description": "",
        "style_description": "",
        "composition": "",
        "color_palette": "",
        "lighting": "",
        "suitable_for": ["main"]
    }


def analyze_images(image_paths: list[str]) -> tuple[str, list[int], list[str], list[dict]]:
    """
    分析图集，返回 (模板描述文本, 代表图编号列表, 代表图路径列表, 每张图的分析结果列表)

    Args:
        image_paths: 图片文件路径列表

    Returns:
        (description, representative_indices, representative_paths, image_analysis_list) - 
        描述文本、代表图编号(1-based)、代表图路径列表、每张图的分析结果
    """
    if not image_paths:
        raise ValueError("请至少上传 1 张图片")

    if len(image_paths) > config.MAX_IMAGES:
        raise ValueError(f"图片数量超过限制，最多 {config.MAX_IMAGES} 张")

    # 构建请求内容：prompt + 所有图片
    system_prompt = _load_prompt()

    parts = [types.Part.from_text(text=system_prompt)]

    for i, path in enumerate(image_paths, 1):
        parts.append(types.Part.from_text(text=f"\n--- 图片 #{i} ---"))
        parts.append(_image_to_part(path))

    parts.append(types.Part.from_text(
        text=f"\n\n以上是全部 {len(image_paths)} 张图片，请开始分析。"
    ))

    # 调用 Gemini
    client = genai.Client(api_key=config.GEMINI_API_KEY)

    response = client.models.generate_content(
        model=config.ANALYSIS_MODEL,
        contents=types.Content(parts=parts, role="user"),
        config=types.GenerateContentConfig(
            temperature=0.3,
            max_output_tokens=4096,
        ),
    )

    result_text = response.text

    # 解析代表图编号
    rep_indices = _parse_representative_images(result_text)

    # 清理描述文本（去掉 REPRESENTATIVE_IMAGES 行和JSON块）
    description = re.sub(
        r"\n*REPRESENTATIVE_IMAGES:\s*\[[^\]]*\]\s*",
        "",
        result_text,
    ).strip()
    description = re.sub(r'```json\s*\n.*?\n```', '', description, flags=re.DOTALL)
    description = re.sub(r'\{[\s\S]*?"has_subject"[\s\S]*?\}', '', description)

    # 获取代表图路径（用于后续作为风格参考图）
    rep_paths = [image_paths[i-1] for i in rep_indices if 1 <= i <= len(image_paths)]

    # 解析每张图的分析结果（简化处理，假设所有图风格一致，取第一个图的JSON）
    analysis_result = _parse_json_fields(result_text)
    
    # 为每张图生成分析结果（基于整体分析）
    image_analysis_list = []
    for i, path in enumerate(image_paths):
        img_analysis = analysis_result.copy()
        img_analysis["image_path"] = path
        img_analysis["image_index"] = i + 1
        img_analysis["is_representative"] = (i + 1) in rep_indices
        image_analysis_list.append(img_analysis)

    return description, rep_indices, rep_paths, image_analysis_list


def analyze_single_image(image_path: str) -> dict:
    """
    分析单张图片，返回结构化分析结果
    
    Args:
        image_path: 图片文件路径
        
    Returns:
        分析结果字典，包含 has_subject, image_type, style_description 等字段
    """
    description, _, _, analysis_list = analyze_images([image_path])
    
    if analysis_list:
        result = analysis_list[0]
        result["full_description"] = description
        return result
    
    return {
        "has_subject": True,
        "image_type": "product",
        "subject_description": "",
        "style_description": "",
        "composition": "",
        "color_palette": "",
        "lighting": "",
        "suitable_for": ["main"],
        "image_path": image_path,
        "image_index": 1,
        "is_representative": True,
        "full_description": description
    }
