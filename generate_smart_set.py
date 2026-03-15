"""
智能批量生成脚本 V3
正确流程：分析(提取风格) → 融合(组装prompt) → 生成(prompt+产品图)
风格通过文字传递，不把参考图传给 generator
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from core.analyzer import analyze_images
from core.fusion import fuse_prompt
from core.generator import generate_image
from core.utils import setup_logging, get_logger

import config

setup_logging()
logger = get_logger("smart_set")

# has_subject=false 时的内容意图模板
STYLE_ONLY_INTENTS = {
    "ecommerce": {
        "ingredient":   "An ingredient diagram for {name}, showing key active ingredients as elegant translucent spheres and molecular structures",
        "efficacy":     "An efficacy infographic for {name}, with clean data visualization and benefit highlights",
        "brand_story":  "A brand story visual for {name}, conveying brand heritage and philosophy",
        "comparison":   "A before-and-after comparison chart for {name}",
        "_default":     "A product illustration for {name}",
    },
    "branding": {
        "brand_palette":    "A brand color palette showcase for {name}",
        "brand_typography": "A typography specimen display for {name}",
        "brand_guideline":  "A brand guideline page for {name}",
        "_default":         "A brand visual design for {name}",
    },
    "marketing": {
        "poster":       "A promotional poster for {name}",
        "banner":       "A web banner graphic for {name}",
        "social_media": "A social media post graphic for {name}",
        "_default":     "A marketing visual for {name}",
    },
    "uiux": {
        "web_ui":   "A web interface design for {name}",
        "app_ui":   "A mobile app interface for {name}",
        "icon":     "An icon design for {name}",
        "_default": "A UI design for {name}",
    },
}

# has_subject=true 时的内容意图模板
PRODUCT_INTENTS = {
    "product_hero": "A hero product shot of {name}, the product bottle/packaging as the main subject, clean and prominent",
    "lifestyle":    "A lifestyle shot of {name}, product in a natural usage context with a model or environment",
    "scene":        "A scene shot of {name}, product elegantly placed in a styled environment",
    "efficacy":     "An efficacy showcase of {name}, product prominently displayed with benefit highlights",
    "comparison":   "A comparison shot of {name}, product shown with before/after or multi-variant display",
    "_default":     "A professional product photograph of {name}",
}


def _get_intent(has_subject: bool, category: str, image_type: str, product_name: str) -> str:
    if has_subject:
        template = PRODUCT_INTENTS.get(image_type, PRODUCT_INTENTS["_default"])
    else:
        cat_intents = STYLE_ONLY_INTENTS.get(category, STYLE_ONLY_INTENTS["ecommerce"])
        template = cat_intents.get(image_type, cat_intents["_default"])
    return template.format(name=product_name)


def _build_rich_style_description(style_info: dict, analysis_list: list, fallback: str,
                                   style_refs: list = None) -> str:
    """
    从 overall_style 的详细字段 + 逐图 style_traits 组装完整风格描述。

    关键：将分析阶段的"图#N"编号重映射为实际传给 generator 的"Style Reference N"编号，
    确保 fusion prompt 中的归因与 generator parts 中的图片顺序一致。

    Args:
        style_refs: 实际传给 generator 的风格参考图路径列表，用于编号映射
    """
    if not style_info:
        return fallback

    # 构建映射：原始图片路径 → Style Reference 编号
    ref_mapping = {}
    if style_refs:
        for sr_idx, sr_path in enumerate(style_refs):
            ref_mapping[os.path.abspath(sr_path)] = f"Style Reference {sr_idx + 1}"

    def _remap_source(source_text: str) -> str:
        """将 '图#1, #3, #5' 格式的引用重映射为 'Style Reference N' 格式。"""
        if not source_text or not ref_mapping or not analysis_list:
            return source_text
        import re
        indices = re.findall(r'#(\d+)', source_text)
        mapped = []
        for idx_str in indices:
            idx = int(idx_str)
            for item in analysis_list:
                if item.get("image_index") == idx:
                    abs_path = os.path.abspath(item["image_path"])
                    if abs_path in ref_mapping:
                        mapped.append(ref_mapping[abs_path])
                    break
        return ", ".join(mapped) if mapped else source_text

    parts = []
    summary = style_info.get("style_description", "")
    if summary:
        parts.append(f"Overall: {summary}")

    detail_fields = [
        ("color_palette", "Color and tone", "color_source"),
        ("rendering", "Rendering style and texture", "rendering_source"),
        ("lighting", "Lighting", "lighting_source"),
        ("composition", "Composition", None),
        ("mood", "Mood and atmosphere", None),
        ("special_elements", "Special design elements", None),
    ]
    for key, label, source_key in detail_fields:
        val = style_info.get(key, "")
        if val and val != summary:
            source = style_info.get(source_key, "") if source_key else ""
            if source:
                remapped = _remap_source(source)
                parts.append(f"{label}: {val} (source: {remapped})")
            else:
                parts.append(f"{label}: {val}")

    if analysis_list and style_refs:
        trait_lines = []
        for item in analysis_list:
            traits = item.get("style_traits", [])
            if not traits:
                continue
            abs_path = os.path.abspath(item["image_path"])
            sr_label = ref_mapping.get(abs_path)
            if sr_label:
                trait_lines.append(f"{sr_label} traits: {', '.join(traits)}")
        if trait_lines:
            parts.append("Per-image style traits:\n" + "\n".join(trait_lines))

    return "\n".join(parts) if parts else fallback


def smart_generate_set(
    product_image_path: str,
    reference_images_dir: str,
    product_name: str = "Product",
    output_prefix: str = "generated",
):
    ref_images = []
    for ext in ["*.jpg", "*.jpeg", "*.png", "*.webp"]:
        ref_images.extend(Path(reference_images_dir).glob(ext))

    if not ref_images:
        logger.error("未在 %s 找到参考图", reference_images_dir)
        return

    ref_paths = sorted([str(p) for p in ref_images])
    logger.info("找到 %d 张参考图, 产品原图: %s", len(ref_paths), product_image_path)

    # ── 阶段1：分析（提取风格 + 逐张分类） ──
    logger.info("═══ 阶段1：风格分析 ═══")
    try:
        description, rep_indices, rep_paths, analysis_list = analyze_images(ref_paths, detailed=True)
    except Exception:
        logger.exception("图集分析失败")
        return

    logger.info("代表图: %s", rep_indices)
    for item in analysis_list:
        idx = item["image_index"]
        cat = item.get("design_category", "?")
        has = item.get("has_subject", "?")
        typ = item.get("image_type", "?")
        logger.info("  #%d [%s] %s  has_subject=%s", idx, cat, typ, has)

    style_info = analysis_list[0].get("overall_style", {}) if analysis_list else {}

    # ── 阶段2+3：逐张融合 + 生成（文+图一起传） ──
    logger.info("═══ 阶段2+3：逐张融合 & 生成 ═══")
    logger.info("风格参考基础: %d 张代表图 %s", len(rep_paths), [Path(p).name for p in rep_paths])
    results = []

    for item in analysis_list:
        idx = item["image_index"]
        ref_path = item["image_path"]
        has_subject = item.get("has_subject", True)
        image_type = item.get("image_type", "product_hero")
        category = item.get("design_category", "ecommerce")
        filename = Path(ref_path).name

        # 风格参考图 = 代表图 + 当前图（去重）
        style_refs = list(rep_paths)
        if ref_path not in style_refs:
            style_refs.append(ref_path)

        # 每次用当前 style_refs 重建风格描述，确保"Style Reference N"编号与 generator 一致
        style_text = _build_rich_style_description(style_info, analysis_list, description[:500], style_refs=style_refs)

        intent = _get_intent(has_subject, category, image_type, product_name)

        if has_subject:
            logger.info("#%d %s | %s | %s | 风格%d张+产品图+融合prompt", idx, filename, category, image_type, len(style_refs))
        else:
            logger.info("#%d %s | %s | %s | 风格%d张+融合prompt(无产品图)", idx, filename, category, image_type, len(style_refs))

        # 阶段2：融合（Sandwich Strategy: 风格文字 + 内容意图 + 参考图数量 → 三层 prompt）
        logger.info("  融合 prompt (Sandwich Strategy, %d 张风格参考)...", len(style_refs))
        try:
            fused_prompt = fuse_prompt(style_text, intent, ref_count=len(style_refs))
            logger.info("  融合结果: %s...", fused_prompt[:100])
        except Exception as e:
            logger.error("  融合失败: %s", e)
            continue

        # 阶段3：生成（融合prompt + 风格参考图 + 产品图，文+图一起传）
        logger.info("  生成图片...")
        try:
            if has_subject:
                paths = generate_image(
                    prompt=fused_prompt,
                    style_references=style_refs,
                    product_reference=product_image_path,
                    aspect_ratio="3:4",
                )
            else:
                paths = generate_image(
                    prompt=fused_prompt,
                    style_references=style_refs,
                    aspect_ratio="3:4",
                )
            results.append({
                "reference": filename,
                "mode": "product+style" if has_subject else "style_only",
                "category": category,
                "type": image_type,
                "outputs": paths,
            })
            logger.info("  生成成功: %d 张", len(paths))
        except Exception as e:
            logger.error("  生成失败: %s", e)

    product_count = sum(1 for r in results if r["mode"] == "product+style")
    style_count = sum(1 for r in results if r["mode"] == "style_only")
    logger.info("全部完成! %d 张 (产品图模式 %d, 纯风格模式 %d)", len(results), product_count, style_count)
    logger.info("输出目录: %s", config.OUTPUT_DIR)
    return results


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="智能批量生成套图 V3")
    parser.add_argument("--product", "-p", required=True, help="产品/品牌原图路径")
    parser.add_argument("--references", "-r", required=True, help="参考图集目录")
    parser.add_argument("--name", "-n", default="Product", help="产品/品牌名称")
    parser.add_argument("--prefix", default="smart", help="输出文件名前缀")
    args = parser.parse_args()

    smart_generate_set(
        product_image_path=args.product,
        reference_images_dir=args.references,
        product_name=args.name,
        output_prefix=args.prefix,
    )
