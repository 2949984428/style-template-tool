"""
阶段3：图片生成器
调用 Gemini 图片生成 API，传入参考图 + 融合 prompt，生成图片
"""

import os
import time
from io import BytesIO
from PIL import Image
from google.genai import types

import config
from core.utils import read_image_bytes, get_client, get_logger, GenerationError

logger = get_logger("generator")


def generate_image(
    prompt: str,
    style_references: list = None,
    product_reference: str = None,
    aspect_ratio: str = None,
) -> list:
    """
    调用 Gemini 生成图片（双参考图模式）。

    Args:
        prompt: 最终融合后的生图 prompt
        style_references: 风格参考图路径列表
        product_reference: 产品参考图路径（用于主体复原）
        aspect_ratio: 宽高比，如 "1:1", "16:9", "3:4"

    Returns:
        生成的图片保存路径列表
    """
    if not prompt.strip():
        raise GenerationError("生成 prompt 不能为空")

    aspect_ratio = aspect_ratio or config.DEFAULT_ASPECT_RATIO
    logger.info(
        "生成图片 (ratio=%s, style_refs=%d, product_ref=%s)",
        aspect_ratio,
        len(style_references) if style_references else 0,
        "yes" if product_reference else "no",
    )

    parts = [
        types.Part.from_text(text=f"Create a professional product photograph: {prompt}")
    ]

    if style_references:
        parts.append(types.Part.from_text(
            text="\nStyle reference images (learn the visual style from these):"
        ))
        for img_path in style_references:
            data, mime_type = read_image_bytes(img_path)
            parts.append(types.Part.from_bytes(data=data, mime_type=mime_type))

    if product_reference and os.path.exists(product_reference):
        parts.append(types.Part.from_text(
            text="\nProduct reference image (maintain this exact product):"
        ))
        data, mime_type = read_image_bytes(product_reference)
        parts.append(types.Part.from_bytes(data=data, mime_type=mime_type))

    client = get_client()
    response = client.models.generate_content(
        model=config.IMAGE_MODEL,
        contents=types.Content(parts=parts, role="user"),
        config=types.GenerateContentConfig(
            response_modalities=["TEXT", "IMAGE"],
            temperature=0.8,
            image_config=types.ImageConfig(aspect_ratio=aspect_ratio),
        ),
    )

    os.makedirs(config.OUTPUT_DIR, exist_ok=True)
    saved_paths = []
    timestamp = int(time.time())

    for i, part in enumerate(response.candidates[0].content.parts):
        if part.inline_data and part.inline_data.mime_type.startswith("image/"):
            ext = ".png" if "png" in part.inline_data.mime_type else ".jpg"
            filename = f"generated_{timestamp}_{i}{ext}"
            filepath = os.path.join(config.OUTPUT_DIR, filename)
            image = Image.open(BytesIO(part.inline_data.data))
            image.save(filepath)
            saved_paths.append(filepath)

    if not saved_paths:
        text_parts = [p.text for p in response.candidates[0].content.parts if p.text]
        raise GenerationError(f"模型未返回图片。模型回复：{''.join(text_parts)}")

    logger.info("生成完成，共 %d 张图片", len(saved_paths))
    return saved_paths
