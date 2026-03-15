"""
阶段2：Prompt 组装器
全代码拼装最终 prompt，结构与示例对齐，不依赖 LLM 生成 prompt
"""

import os
from core.utils import get_logger, FusionError

logger = get_logger("fusion")


def fuse_prompt(
    template_description: str,
    user_prompt: str,
    ref_count: int = 1,
    product_description: str = "",
    exclude_items: str = "",
    style_info: dict = None,
) -> str:
    """
    代码拼装最终生图 prompt，与示例结构对齐：
    [产品+意图 from Ref 1] + [产品细节] + [风格锚定 Ref 2+] + [风格叙述] + [排除项]

    Args:
        template_description: 风格描述文本（fallback 用）
        user_prompt: 内容意图
        ref_count: 风格参考图数量
        product_description: 产品外观描述（可选）
        exclude_items: 排除元素
        style_info: overall_style dict（用于结构化拼装风格叙述）
    """
    if not user_prompt.strip():
        raise FusionError("用户 prompt 不能为空")

    # === Part 1: 产品+意图 ===
    intent = user_prompt.strip()
    if intent.startswith(("A ", "An ", "a ", "an ")):
        part1 = f"{intent} from Reference Image 1."
    else:
        part1 = f"A high-quality {intent} from Reference Image 1."

    # === Part 2: 产品细节 ===
    part2 = ""
    if product_description:
        part2 = f" Maintain the product's precise visual details: {product_description}."

    # === Part 3: 风格锚定 ===
    if ref_count == 1:
        ref_label = "Reference Image 2"
    elif ref_count == 2:
        ref_label = "Reference Image 2 and Reference Image 3"
    else:
        refs = [f"Reference Image {i+2}" for i in range(ref_count)]
        ref_label = ", ".join(refs[:-1]) + " and " + refs[-1]

    part3 = (
        f" Strictly apply the visual style derived from Style Reference: {ref_label}."
        f" The image must look like it belongs to the same visual series."
    )

    # === Part 4: 风格叙述（代码拼装） ===
    part4 = _build_style_narration(style_info, template_description, ref_count)

    # === Part 5: 排除项 ===
    if exclude_items:
        part5 = (
            f" Do not include {exclude_items};"
            f" the core product identity must remain strictly from Reference Image 1."
        )
    else:
        part5 = (
            " Do not include any brand names, logos, text, or graphic elements"
            " from the style references;"
            " the core product identity must remain strictly from Reference Image 1."
        )

    full_prompt = part1 + part2 + part3 + part4 + part5
    word_count = len(full_prompt.split())
    logger.info("融合完成: %d 词", word_count)
    return full_prompt


def _build_style_narration(style_info: dict, fallback_text: str, ref_count: int) -> str:
    """从 style_info 结构化数据拼装英文风格叙述段。"""
    if not style_info:
        return f" {fallback_text[:500]}" if fallback_text else ""

    sentences = []

    # 光影
    lighting = style_info.get("lighting", "")
    lighting_src = style_info.get("lighting_source", "")
    if lighting:
        src = _format_source(lighting_src, ref_count)
        sentences.append(
            f"Apply the lighting aesthetic of the style references to the central subject — "
            f"{_to_english_brief(lighting)}"
            f"{src}, creating soft, elegant highlights and shadows "
            f"that give the product a premium, three-dimensional feel."
        )

    # 色彩
    color = style_info.get("color_palette", "")
    color_src = style_info.get("color_source", "")
    if color:
        src = _format_source(color_src, ref_count)
        sentences.append(
            f"Utilize a harmonious color palette — {_to_english_brief(color)}"
            f"{src} — to seamlessly complement the product's design."
        )

    # 渲染/质感
    rendering = style_info.get("rendering", "")
    rendering_src = style_info.get("rendering_source", "")
    if rendering:
        src = _format_source(rendering_src, ref_count)
        sentences.append(
            f"The rendering and material quality should reflect "
            f"{_to_english_brief(rendering)}"
            f"{src}."
        )

    # 氛围
    mood = style_info.get("mood", "")
    if mood:
        sentences.append(
            f"The overall mood should convey {_to_english_brief(mood)}, "
            f"emphasizing the product's clean, professional, yet approachable character."
        )

    # 构图
    composition = style_info.get("composition", "")
    if composition:
        sentences.append(
            f"Compositionally, follow {_to_english_brief(composition)}."
        )

    if not sentences:
        return f" {fallback_text[:300]}" if fallback_text else ""

    return " " + " ".join(sentences)


def _format_source(source_text: str, ref_count: int) -> str:
    """将 'Style Reference 1, Style Reference 2' 格式化为引用标注。"""
    if not source_text:
        return ""
    import re
    refs = re.findall(r'Style Reference (\d+)', source_text)
    if refs:
        labels = [f"Reference Image {int(r)+1}" for r in refs]
        return f", as seen in {' and '.join(labels)}"
    return ""


def _to_english_brief(chinese_text: str) -> str:
    """保留文本原样（分析阶段已可能含英文），截断过长的内容。"""
    text = chinese_text.strip()
    if len(text) > 300:
        text = text[:300] + "..."
    return text
