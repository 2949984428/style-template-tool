"""
阶段3：图片生成器
调用 Gemini 图片生成 API，传入参考图 + 融合 prompt，生成图片
"""

import os
import time
from PIL import Image
from google import genai
from google.genai import types

import config


def generate_image(
    prompt: str,
    style_references: list[str] = None,
    product_reference: str = None,
    aspect_ratio: str = None,
) -> list[str]:
    """
    调用 Gemini 生成图片（双参考图模式）

    Args:
        prompt: 最终融合后的生图 prompt
        style_references: 风格参考图路径列表（来自模板的代表图）
        product_reference: 产品参考图路径（用户上传的产品图）
        aspect_ratio: 宽高比，如 "1:1", "16:9", "4:3"

    Returns:
        生成的图片保存路径列表
    """
    if not prompt.strip():
        raise ValueError("生成 prompt 不能为空")

    aspect_ratio = aspect_ratio or config.DEFAULT_ASPECT_RATIO

    # 构建请求内容 - 双参考图模式
    # 风格参考图（style_references）+ 产品参考图（product_reference）
    parts = []
    
    # 首先添加明确的生成指令（英文效果更好）
    parts.append(types.Part.from_text(
        text=f"Create a professional product photograph: {prompt}"
    ))

    # 添加风格参考图（作为风格参考 - 学习视觉风格）
    if style_references:
        parts.append(types.Part.from_text(
            text="\nStyle reference images (learn the visual style from these):"
        ))
        for img_path in style_references:
            with open(img_path, "rb") as f:
                data = f.read()
            ext = os.path.splitext(img_path)[1].lower()
            mime_map = {
                ".jpg": "image/jpeg",
                ".jpeg": "image/jpeg",
                ".png": "image/png",
                ".webp": "image/webp",
            }
            mime_type = mime_map.get(ext, "image/jpeg")
            parts.append(types.Part.from_bytes(data=data, mime_type=mime_type))

    # 添加产品参考图（作为 object fidelity - 保持产品一致性）
    if product_reference and os.path.exists(product_reference):
        parts.append(types.Part.from_text(
            text="\nProduct reference image (maintain this exact product):"
        ))
        with open(product_reference, "rb") as f:
            data = f.read()
        ext = os.path.splitext(product_reference)[1].lower()
        mime_map = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".webp": "image/webp",
        }
        mime_type = mime_map.get(ext, "image/jpeg")
        parts.append(types.Part.from_bytes(data=data, mime_type=mime_type))

    # 调用 Gemini 图片生成
    client = genai.Client(api_key=config.GEMINI_API_KEY)

    response = client.models.generate_content(
        model=config.IMAGE_MODEL,
        contents=types.Content(parts=parts, role="user"),
        config=types.GenerateContentConfig(
            response_modalities=["TEXT", "IMAGE"],
            temperature=0.8,
            image_config=types.ImageConfig(
                aspect_ratio=aspect_ratio,
            ),
        ),
    )

    # 解析响应，提取生成的图片
    os.makedirs(config.OUTPUT_DIR, exist_ok=True)
    saved_paths = []
    timestamp = int(time.time())

    for i, part in enumerate(response.candidates[0].content.parts):
        if part.inline_data and part.inline_data.mime_type.startswith("image/"):
            ext = ".png" if "png" in part.inline_data.mime_type else ".jpg"
            filename = f"generated_{timestamp}_{i}{ext}"
            filepath = os.path.join(config.OUTPUT_DIR, filename)

            # 从 base64 数据保存图片
            image = Image.open(
                __import__("io").BytesIO(part.inline_data.data)
            )
            image.save(filepath)
            saved_paths.append(filepath)

    if not saved_paths:
        # 如果没有图片，可能模型返回了纯文本
        text_parts = [p.text for p in response.candidates[0].content.parts if p.text]
        raise RuntimeError(
            f"模型未返回图片。模型回复：{''.join(text_parts)}"
        )

    return saved_paths
