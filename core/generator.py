"""
阶段3：图片生成器
直接调用 Gemini REST API，文+图一起传

关键：prompt 明确区分"学什么"和"不学什么"，防止模型把参考图当素材合成
"""

import os
import time
import base64
import requests
from io import BytesIO
from PIL import Image

import config
from core.utils import read_image_bytes, get_logger, GenerationError

logger = get_logger("generator")

API_BASE = "https://generativelanguage.googleapis.com/v1beta/models"


def _image_to_inline_data(image_path: str) -> dict:
    data, mime_type = read_image_bytes(image_path)
    return {"inline_data": {"mime_type": mime_type, "data": base64.b64encode(data).decode()}}


def generate_image(
    prompt: str,
    style_references: list = None,
    product_reference: str = None,
    aspect_ratio: str = None,
    image_size: str = None,
) -> list:
    """
    文+图一起传给 Gemini 生成图片。

    Args:
        prompt: 融合后的生图 prompt（已包含详细风格描述）
        style_references: 风格参考图路径列表（模型从中学习视觉风格）
        product_reference: 产品原图路径（模型保持产品外观一致）
        aspect_ratio: 宽高比
        image_size: 分辨率 "512", "1K", "2K", "4K"
    """
    if not prompt.strip():
        raise GenerationError("生成 prompt 不能为空")

    aspect_ratio = aspect_ratio or config.DEFAULT_ASPECT_RATIO
    image_size = image_size or config.DEFAULT_IMAGE_SIZE
    n_style = len(style_references) if style_references else 0

    logger.info(
        "生成图片 (ratio=%s, size=%s, style_refs=%d, product_ref=%s)",
        aspect_ratio, image_size, n_style,
        "yes" if product_reference else "no",
    )

    # ── 构建 parts：产品图(Image 1) → 风格参考图 → 文本指令 ──
    parts = []

    if product_reference and os.path.exists(product_reference):
        parts.append(_image_to_inline_data(product_reference))

    if style_references:
        for img_path in style_references:
            parts.append(_image_to_inline_data(img_path))

    instruction = _build_instruction(prompt, n_style, product_reference)
    parts.append({"text": instruction})

    payload = {
        "contents": [{"parts": parts}],
        "generationConfig": {
            "responseModalities": ["TEXT", "IMAGE"],
            "imageConfig": {
                "aspectRatio": aspect_ratio,
                "imageSize": image_size,
            },
        },
    }

    url = f"{API_BASE}/{config.IMAGE_MODEL}:generateContent"
    headers = {
        "x-goog-api-key": config.GEMINI_API_KEY,
        "Content-Type": "application/json",
    }

    resp = requests.post(url, json=payload, headers=headers, timeout=180)

    if resp.status_code != 200:
        raise GenerationError(f"API 返回 {resp.status_code}: {resp.text[:500]}")

    result = resp.json()
    if "candidates" not in result or not result["candidates"]:
        raise GenerationError(f"API 未返回 candidates: {str(result)[:500]}")

    os.makedirs(config.OUTPUT_DIR, exist_ok=True)
    saved_paths = []
    timestamp = int(time.time())

    response_parts = result["candidates"][0].get("content", {}).get("parts", [])
    for i, part in enumerate(response_parts):
        if part.get("thought"):
            continue
        inline = part.get("inlineData") or part.get("inline_data")
        if inline and inline.get("mimeType", inline.get("mime_type", "")).startswith("image/"):
            mime = inline.get("mimeType") or inline.get("mime_type")
            img_data = base64.b64decode(inline["data"])
            ext = ".png" if "png" in mime else ".jpg"
            filename = f"generated_{timestamp}_{i}{ext}"
            filepath = os.path.join(config.OUTPUT_DIR, filename)
            image = Image.open(BytesIO(img_data))
            image.save(filepath)
            saved_paths.append(filepath)
            logger.info("  保存: %s (%dx%d)", filename, image.width, image.height)

    if not saved_paths:
        text_parts = [p.get("text", "") for p in response_parts if p.get("text") and not p.get("thought")]
        raise GenerationError(f"模型未返回图片。模型回复：{''.join(text_parts)}")

    logger.info("生成完成，共 %d 张图片", len(saved_paths))
    return saved_paths


def _build_instruction(prompt: str, n_style: int, product_reference: str) -> str:
    """
    构建最终传给模型的文本指令。

    prompt 已经是 Sandwich Strategy 三层结构（由 fusion 阶段产出），
    这里只添加"图像角色声明"和"硬约束"框架，让模型知道每张图是什么角色。
    """

    if n_style > 0 and product_reference:
        ref_labels = ", ".join(f"Style Reference {i+1}" for i in range(n_style))
        return (
            f"[IMAGE ROLES]\n"
            f"- Image 1: PRODUCT (the item to photograph) — preserve its exact appearance (shape, label, packaging text, colors)\n"
            f"- Images 2-{n_style + 1}: STYLE REFERENCES ({ref_labels})\n"
            f"\n"
            f"[HARD CONSTRAINTS]\n"
            f"- The output must feature ONLY the product from Image 1.\n"
            f"- Do NOT copy any text, brand names, logos, slogans, or graphic elements from the style references.\n"
            f"- Do NOT reproduce the specific product/packaging shown in the style references.\n"
            f"\n"
            f"[GENERATION PROMPT]\n"
            f"{prompt}"
        )

    elif n_style > 0:
        ref_labels = ", ".join(f"Style Reference {i+1}" for i in range(n_style))
        return (
            f"[IMAGE ROLES]\n"
            f"- Images 1-{n_style}: STYLE REFERENCES ({ref_labels})\n"
            f"\n"
            f"[HARD CONSTRAINTS]\n"
            f"- Do NOT copy any text, brand names, logos, or specific content from the references.\n"
            f"- Learn ONLY the visual style language from them.\n"
            f"\n"
            f"[GENERATION PROMPT]\n"
            f"{prompt}"
        )

    elif product_reference:
        return (
            f"[IMAGE ROLES]\n"
            f"- Image 1: PRODUCT — preserve its exact appearance (shape, label, packaging text, colors)\n"
            f"\n"
            f"[GENERATION PROMPT]\n"
            f"{prompt}"
        )

    else:
        return prompt
