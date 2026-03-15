"""
智能批量生成脚本 V2
根据参考图的 design_category + has_subject 自动选择生成策略
支持电商、品牌、营销、UI/UX 等不同垂类
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from core.analyzer import analyze_images
from core.generator import generate_image
from core.utils import setup_logging, get_logger

import config

setup_logging()
logger = get_logger("smart_set")

STYLE_ONLY_PROMPTS = {
    "ecommerce": {
        "ingredient":   "{name} ingredient diagram, showing key ingredients and benefits, {style}",
        "efficacy":     "{name} efficacy infographic, data visualization with clean layout, {style}",
        "brand_story":  "{name} brand story visual, brand heritage and philosophy, {style}",
        "comparison":   "{name} before and after comparison chart, {style}",
        "_default":     "{name} product illustration, {style}",
    },
    "branding": {
        "brand_palette":    "{name} brand color palette, color system showcase, {style}",
        "brand_typography": "{name} typography specimen, font pairing display, {style}",
        "brand_guideline":  "{name} brand guideline page, usage specification, {style}",
        "_default":         "{name} brand visual, {style}",
    },
    "marketing": {
        "poster":       "{name} promotional poster, {style}",
        "banner":       "{name} web banner graphic, {style}",
        "social_media": "{name} social media post graphic, {style}",
        "_default":     "{name} marketing visual, {style}",
    },
    "uiux": {
        "web_ui":   "{name} web interface design, {style}",
        "app_ui":   "{name} mobile app interface, {style}",
        "icon":     "{name} icon design, {style}",
        "_default": "{name} UI design, {style}",
    },
}


def _get_style_only_prompt(category: str, image_type: str, product_name: str, style_desc: str) -> str:
    cat_prompts = STYLE_ONLY_PROMPTS.get(category, STYLE_ONLY_PROMPTS["ecommerce"])
    template = cat_prompts.get(image_type, cat_prompts["_default"])
    return template.format(name=product_name, style=style_desc)


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

    logger.info("分析图集 (详细模式)...")
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
        mode = "双参考图" if has else "单参考图"
        logger.info("  #%d [%s] %s  has_subject=%s → %s", idx, cat, typ, has, mode)

    logger.info("开始逐张生成")
    style_desc = description[:200] if description else ""
    results = []

    for item in analysis_list:
        idx = item["image_index"]
        ref_path = item["image_path"]
        has_subject = item.get("has_subject", True)
        image_type = item.get("image_type", "product_hero")
        category = item.get("design_category", "ecommerce")
        style_info = item.get("overall_style", {})
        sd = style_info.get("style_description", style_desc) if style_info else style_desc

        filename = Path(ref_path).name
        mode_label = "双参考图" if has_subject else "单参考图"
        logger.info("#%d %s | %s | %s | %s", idx, filename, category, image_type, mode_label)

        if has_subject:
            prompt_text = f"{product_name} professional {image_type} photography, {sd}"
            try:
                paths = generate_image(
                    prompt=prompt_text,
                    style_references=[ref_path],
                    product_reference=product_image_path,
                    aspect_ratio="3:4",
                )
                results.append({"reference": filename, "mode": "dual", "category": category, "type": image_type, "outputs": paths})
                logger.info("  生成成功: %d 张", len(paths))
            except Exception as e:
                logger.error("  生成失败: %s", e)
        else:
            prompt_text = _get_style_only_prompt(category, image_type, product_name, sd)
            try:
                paths = generate_image(
                    prompt=prompt_text,
                    style_references=[ref_path],
                    product_reference=None,
                    aspect_ratio="3:4",
                )
                results.append({"reference": filename, "mode": "single", "category": category, "type": image_type, "outputs": paths})
                logger.info("  生成成功: %d 张", len(paths))
            except Exception as e:
                logger.error("  生成失败: %s", e)

    dual = sum(1 for r in results if r["mode"] == "dual")
    single = sum(1 for r in results if r["mode"] == "single")
    logger.info("全部完成! %d 张 (双参考图 %d, 单参考图 %d)", len(results), dual, single)
    logger.info("输出目录: %s", config.OUTPUT_DIR)
    return results


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="智能批量生成套图（支持多垂类）")
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
