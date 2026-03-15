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
    product_reference: str = None,
    aspect_ratio: str = None,
    image_size: str = None,
) -> list:
    """
    直接调用 Gemini REST API 生成图片。

    风格通过 prompt 文字传递（来自 fusion 阶段），不通过参考图。
    product_reference 仅用于让模型保持产品外观一致。

    Args:
        prompt: 融合后的生图 prompt（已包含风格描述）
        product_reference: 产品原图路径（has_subject=true 时使用）
        aspect_ratio: 宽高比
        image_size: 分辨率 "512", "1K", "2K", "4K"
    """
    if not prompt.strip():
        raise GenerationError("生成 prompt 不能为空")

    aspect_ratio = aspect_ratio or config.DEFAULT_ASPECT_RATIO
    image_size = image_size or config.DEFAULT_IMAGE_SIZE

    logger.info(
        "生成图片 (ratio=%s, size=%s, product_ref=%s)",
        aspect_ratio, image_size,
        "yes" if product_reference else "no",
    )

    parts = []

    if product_reference and os.path.exists(product_reference):
        parts.append(_image_to_inline_data(product_reference))
        instruction = (
            f"Create a new product photograph using the provided product image as the subject. "
            f"Maintain the exact product appearance (shape, label, colors, logo) from the image. "
            f"Do NOT copy any text, branding, or layout from anywhere else. "
            f"Apply the following visual style to create a completely new composition:\n\n{prompt}"
        )
    else:
        instruction = prompt

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
