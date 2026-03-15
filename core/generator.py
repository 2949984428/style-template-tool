"""
阶段3：图片生成器
调用 Gemini 图片生成 API，传入参考图 + 融合 prompt，生成图片

对齐官方文档 https://ai.google.dev/gemini-api/docs/image-generation
- 图片在前、文本指令在后（高保真模式）
- 支持 image_size (512/1K/2K/4K)
- 支持 thinking_config (minimal/high)
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
    image_size: str = None,
) -> list:
    """
    调用 Gemini 生成图片（双参考图模式）。

    官方推荐：图片 Part 在前，文本指令在后。
    参考：https://ai.google.dev/gemini-api/docs/image-generation

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
    logger.info(
        "生成图片 (ratio=%s, size=%s, style_refs=%d, product_ref=%s)",
        aspect_ratio,
        image_size,
        len(style_references) if style_references else 0,
        "yes" if product_reference else "no",
    )

    # 官方推荐顺序：参考图片在前，文本指令在后
    parts = []

    if style_references:
        for img_path in style_references:
            data, mime_type = read_image_bytes(img_path)
            parts.append(types.Part.from_bytes(data=data, mime_type=mime_type))

    if product_reference and os.path.exists(product_reference):
        data, mime_type = read_image_bytes(product_reference)
        parts.append(types.Part.from_bytes(data=data, mime_type=mime_type))

    n_style = len(style_references) if style_references else 0

    if style_references and product_reference:
        style_part = (
            f"the first {n_style} images" if n_style > 1
            else "the first image"
        )
        product_part = "the last image"
        instruction = (
            f"Using the visual style, color palette, lighting, and texture from {style_part} as style reference, "
            f"and maintaining the exact product appearance from {product_part}, "
            f"create a professional product photograph: {prompt}"
        )
    elif style_references:
        style_part = (
            f"the provided {n_style} reference images" if n_style > 1
            else "the provided reference image"
        )
        instruction = (
            f"Using the visual style, color palette, lighting, and texture from {style_part}, "
            f"create a professional product illustration: {prompt}"
        )
    else:
        instruction = f"Create a professional product photograph: {prompt}"

    parts.append(types.Part.from_text(text=instruction))

    client = get_client()
    response = client.models.generate_content(
        model=config.IMAGE_MODEL,
        contents=types.Content(parts=parts, role="user"),
        config=types.GenerateContentConfig(
            response_modalities=["TEXT", "IMAGE"],
            temperature=0.8,
            image_config=types.ImageConfig(
                aspect_ratio=aspect_ratio,
                image_size=image_size,
            ),
            thinking_config=types.ThinkingConfig(
                thinking_level=config.DEFAULT_THINKING_LEVEL,
            ),
        ),
    )

    os.makedirs(config.OUTPUT_DIR, exist_ok=True)
    saved_paths = []
    timestamp = int(time.time())

    for i, part in enumerate(response.candidates[0].content.parts):
        if getattr(part, 'thought', False):
            continue
        if part.inline_data and part.inline_data.mime_type.startswith("image/"):
            ext = ".png" if "png" in part.inline_data.mime_type else ".jpg"
            filename = f"generated_{timestamp}_{i}{ext}"
            filepath = os.path.join(config.OUTPUT_DIR, filename)
            image = Image.open(BytesIO(part.inline_data.data))
            image.save(filepath)
            saved_paths.append(filepath)

    if not saved_paths:
        text_parts = [p.text for p in response.candidates[0].content.parts if p.text and not getattr(p, 'thought', False)]
        raise GenerationError(f"模型未返回图片。模型回复：{''.join(text_parts)}")

    logger.info("生成完成，共 %d 张图片", len(saved_paths))
    return saved_paths
