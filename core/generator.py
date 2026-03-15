"""
阶段3：图片生成器
直接调用 Gemini REST API 生成图片，绕过 SDK Pydantic 校验限制

对齐官方文档 https://ai.google.dev/gemini-api/docs/image-generation
- 图片在前、文本指令在后（高保真模式）
- 支持 image_size (512/1K/2K/4K)
- 支持 thinking_config (minimal/high)
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
    直接调用 Gemini REST API 生成图片。

    Args:
        prompt: 最终融合后的生图 prompt
        style_references: 风格参考图路径列表
        product_reference: 产品参考图路径（用于主体复原）
        aspect_ratio: 宽高比，如 "1:1", "16:9", "3:4"
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

    # 构建 parts：图片在前，文本指令在后（官方推荐）
    parts = []

    if style_references:
        for img_path in style_references:
            parts.append(_image_to_inline_data(img_path))

    if product_reference and os.path.exists(product_reference):
        parts.append(_image_to_inline_data(product_reference))

    if style_references and product_reference:
        style_label = f"the first {n_style} images" if n_style > 1 else "the first image"
        instruction = (
            f"Using the visual style, color palette, lighting, and texture from {style_label} as style reference, "
            f"and maintaining the exact product appearance from the last image, "
            f"create a professional product photograph: {prompt}"
        )
    elif style_references:
        style_label = f"the provided {n_style} reference images" if n_style > 1 else "the provided reference image"
        instruction = (
            f"Using the visual style, color palette, lighting, and texture from {style_label}, "
            f"create a professional product illustration: {prompt}"
        )
    else:
        instruction = f"Create a professional product photograph: {prompt}"

    parts.append({"text": instruction})

    # 构建请求体
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

    # 解析返回的图片
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
