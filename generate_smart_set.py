"""
智能批量生成脚本 V2
根据参考图的 has_subject 字段自动选择单/双参考图模式
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from core.analyzer_v2 import analyze_single_image
from core.fusion import fuse_prompt
from core.generator import generate_image

import config


def smart_generate_set(
    product_image_path: str,
    reference_images_dir: str,
    product_name: str = "Product",
    output_prefix: str = "generated"
):
    """
    智能生成电商套图
    
    Args:
        product_image_path: 用户产品原图路径（用于主体复原）
        reference_images_dir: 参考图集目录
        product_name: 产品名称
        output_prefix: 输出文件名前缀
    """
    
    # 1. 收集所有参考图
    reference_images = []
    for ext in ['*.jpg', '*.jpeg', '*.png', '*.webp']:
        reference_images.extend(Path(reference_images_dir).glob(ext))
    
    if not reference_images:
        print(f"未在 {reference_images_dir} 找到参考图")
        return
    
    print(f"找到 {len(reference_images)} 张参考图")
    print(f"产品原图: {product_image_path}")
    print("-" * 50)
    
    # 2. 分析每张参考图并生成
    results = []
    
    for i, ref_path in enumerate(reference_images, 1):
        print(f"\n处理第 {i}/{len(reference_images)} 张参考图: {ref_path.name}")
        
        # 2.1 分析参考图
        try:
            analysis = analyze_single_image(str(ref_path))
        except Exception as e:
            print(f"  分析失败: {e}")
            continue
        
        has_subject = analysis.get("has_subject", True)
        image_type = analysis.get("image_type", "product")
        style_desc = analysis.get("style_description", "")
        
        print(f"  类型: {image_type}")
        print(f"  包含主体: {has_subject}")
        
        # 2.2 根据 has_subject 选择生成模式
        if has_subject:
            # 双参考图模式：风格 + 产品复原
            print(f"  模式: 双参考图（风格+产品）")
            try:
                result_paths = generate_image(
                    prompt=f"{product_name} product photography, {style_desc}",
                    style_references=[str(ref_path)],
                    product_reference=product_image_path,
                    aspect_ratio='3:4'
                )
                results.append({
                    "reference": ref_path.name,
                    "mode": "dual",
                    "type": image_type,
                    "outputs": result_paths
                })
                print(f"  生成成功: {len(result_paths)} 张")
            except Exception as e:
                print(f"  生成失败: {e}")
        else:
            # 单参考图模式：只学风格，不强制产品复原
            print(f"  模式: 单参考图（仅风格）")
            try:
                # 构建适合该类型的prompt
                if image_type == "ingredient":
                    prompt = f"{product_name} ingredient diagram, showing key ingredients and benefits, {style_desc}"
                elif image_type == "scene":
                    prompt = f"{product_name} lifestyle scene, showing usage context, {style_desc}"
                elif image_type == "background":
                    prompt = f"{product_name} background texture, {style_desc}"
                else:
                    prompt = f"{product_name} illustration, {style_desc}"
                
                result_paths = generate_image(
                    prompt=prompt,
                    style_references=[str(ref_path)],
                    product_reference=None,  # 不传递产品参考
                    aspect_ratio='3:4'
                )
                results.append({
                    "reference": ref_path.name,
                    "mode": "single",
                    "type": image_type,
                    "outputs": result_paths
                })
                print(f"  生成成功: {len(result_paths)} 张")
            except Exception as e:
                print(f"  生成失败: {e}")
    
    # 3. 输出总结
    print("\n" + "=" * 50)
    print("生成完成!")
    print(f"总计: {len(results)} 张参考图处理成功")
    
    dual_count = sum(1 for r in results if r["mode"] == "dual")
    single_count = sum(1 for r in results if r["mode"] == "single")
    print(f"  - 双参考图模式: {dual_count} 张")
    print(f"  - 单参考图模式: {single_count} 张")
    
    print(f"\n输出目录: {config.OUTPUT_DIR}")
    
    return results


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='智能批量生成电商套图')
    parser.add_argument('--product', '-p', required=True, help='产品原图路径')
    parser.add_argument('--references', '-r', required=True, help='参考图集目录')
    parser.add_argument('--name', '-n', default='Product', help='产品名称')
    parser.add_argument('--prefix', default='smart', help='输出文件名前缀')
    
    args = parser.parse_args()
    
    smart_generate_set(
        product_image_path=args.product,
        reference_images_dir=args.references,
        product_name=args.name,
        output_prefix=args.prefix
    )
