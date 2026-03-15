"""
图集分析器（合并 V1 + V2）
- 基础模式 (默认): 返回 (description, rep_indices, rep_paths)
- 详细模式 (detailed=True): 额外返回每张图的独立分类结果
"""

import os
import re
import json
from google.genai import types

import config
from core.utils import image_to_part, get_client, get_logger, AnalysisError

logger = get_logger("analyzer")

PROMPTS_DIR = os.path.join(os.path.dirname(__file__), "..", "prompts")


def _load_prompt(version: str = "v1") -> str:
    filename = "analyze_v2.txt" if version == "v2" else "analyze.txt"
    path = os.path.join(PROMPTS_DIR, filename)
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def _parse_representative_images(text: str) -> list:
    match = re.search(r"REPRESENTATIVE_IMAGES:\s*\[([^\]]+)\]", text)
    if match:
        return [int(n) for n in re.findall(r"\d+", match.group(1))]
    return [1]


def _parse_json_response(text: str, image_count: int) -> tuple:
    parsed = None

    for m in re.finditer(r'```json\s*\n(.*?)\n```', text, re.DOTALL):
        try:
            candidate = json.loads(m.group(1))
            if isinstance(candidate, dict) and "per_image" in candidate:
                parsed = candidate
                break
        except json.JSONDecodeError:
            continue

    if parsed is None:
        m = re.search(r'\{[\s\S]*?"per_image"[\s\S]*\}', text)
        if m:
            raw = m.group(0)
            for end in range(len(raw), 0, -1):
                try:
                    candidate = json.loads(raw[:end])
                    if isinstance(candidate, dict) and "per_image" in candidate:
                        parsed = candidate
                        break
                except json.JSONDecodeError:
                    continue

    per_image = parsed.get("per_image", []) if parsed else []
    overall = parsed.get("overall_style", {}) if parsed else {}

    default_item = {
        "design_category": "ecommerce",
        "has_subject": True,
        "image_type": "product_hero",
        "subject_description": "",
    }
    while len(per_image) < image_count:
        per_image.append({**default_item, "image_index": len(per_image) + 1})

    for item in per_image:
        item.setdefault("design_category", "ecommerce")
        item.setdefault("has_subject", True)
        item.setdefault("image_type", "product_hero")
        item.setdefault("subject_description", "")

    return per_image, overall


def _call_gemini(image_paths: list, system_prompt: str) -> str:
    parts = [types.Part.from_text(text=system_prompt)]
    for i, path in enumerate(image_paths, 1):
        parts.append(types.Part.from_text(text=f"\n--- 图片 #{i} ---"))
        parts.append(image_to_part(path))
    parts.append(types.Part.from_text(
        text=f"\n\n以上是全部 {len(image_paths)} 张图片，请开始分析。"
    ))

    client = get_client()
    response = client.models.generate_content(
        model=config.ANALYSIS_MODEL,
        contents=types.Content(parts=parts, role="user"),
        config=types.GenerateContentConfig(temperature=0.3, max_output_tokens=4096),
    )
    return response.text


def analyze_images(image_paths: list, detailed: bool = False) -> tuple:
    """
    基础模式: (description, rep_indices, rep_paths)
    详细模式: (description, rep_indices, rep_paths, image_analysis_list)
    """
    if not image_paths:
        raise AnalysisError("请至少上传 1 张图片")
    if len(image_paths) > config.MAX_IMAGES:
        raise AnalysisError(f"图片数量超过限制，最多 {config.MAX_IMAGES} 张")

    version = "v2" if detailed else "v1"
    logger.info("分析 %d 张图片 (mode=%s)", len(image_paths), version)
    system_prompt = _load_prompt(version)
    result_text = _call_gemini(image_paths, system_prompt)
    logger.debug("Gemini 返回 %d 字符", len(result_text))

    rep_indices = _parse_representative_images(result_text)

    description = re.sub(r"\n*REPRESENTATIVE_IMAGES:\s*\[[^\]]*\]\s*", "", result_text)
    if detailed:
        description = re.sub(r'```json\s*\n.*?\n```', '', description, flags=re.DOTALL)
        description = re.sub(r'\{[\s\S]*?"per_image"[\s\S]*?\}(?:\s*\})?', '', description)
    description = description.strip()

    rep_paths = [image_paths[i - 1] for i in rep_indices if 1 <= i <= len(image_paths)]

    if not detailed:
        return description, rep_indices, rep_paths

    per_image_list, overall_style = _parse_json_response(result_text, len(image_paths))

    analysis_list = []
    for i, path in enumerate(image_paths):
        item = per_image_list[i] if i < len(per_image_list) else {}
        item["image_path"] = path
        item["image_index"] = i + 1
        item["is_representative"] = (i + 1) in rep_indices
        item["overall_style"] = overall_style
        analysis_list.append(item)

    return description, rep_indices, rep_paths, analysis_list


def analyze_single_image(image_path: str) -> dict:
    description, _, _, analysis_list = analyze_images([image_path], detailed=True)
    if analysis_list:
        result = analysis_list[0]
        result["full_description"] = description
        return result
    return {
        "design_category": "ecommerce",
        "has_subject": True,
        "image_type": "product_hero",
        "subject_description": "",
        "overall_style": {},
        "image_path": image_path,
        "image_index": 1,
        "is_representative": True,
        "full_description": description,
    }
