#!/usr/bin/env python3
"""
"做同款"功能完整实现
流程：
1. 作者上传多张参考图（主图、副图等）
2. 自动识别每张图的类型
3. 用户上传产品图
4. 按类型匹配生成同类型图片
"""

import os
import sys
import shutil

sys.path.insert(0, os.path.dirname(__file__))

from core.image_classifier import analyze_uploaded_set, get_scene_prompt_by_type
from core.analyzer import analyze_images
from core.fusion import fuse_prompt
from core.generator import generate_image


def do_the_same(reference_images, product_image, output_dir="outputs/do_the_same"):
    """
    做同款：根据参考图生成同类型的产品图
    
    Args:
        reference_images: 参考图路径列表（作者上传的多张图）
        product_image: 用户上传的产品图
        output_dir: 输出目录
        
    Returns:
        生成结果列表
    """
    print("=" * 70)
    print("🎨 做同款 - 智能类型匹配生成")
    print("=" * 70)
    
    os.makedirs(output_dir, exist_ok=True)
    
    # Step 1: 分析参考图类型
    print("\n📸 Step 1: 分析参考图类型")
    reference_analysis = analyze_uploaded_set(reference_images)
    
    print(f"   共 {len(reference_analysis)} 张参考图")
    for i, ref in enumerate(reference_analysis, 1):
        main_mark = "【主图】" if ref['is_main'] else ""
        print(f"   {i}. {ref['type_name']} {main_mark} (置信度: {ref['confidence']}%)")
        print(f"      文件: {os.path.basename(ref['path'])}")
    
    # Step 2: 按类型分组，提取风格
    print("\n📸 Step 2: 提取各类型风格")
    type_styles = {}
    
    for ref in reference_analysis:
        img_type = ref['type']
        if img_type not in type_styles:
            # 分析该类型的风格
            print(f"   分析 {ref['type_name']} 风格...")
            try:
                desc, _, rep_paths = analyze_images([ref['path']])
                type_styles[img_type] = {
                    'description': desc,
                    'representative': rep_paths,
                    'reference': ref
                }
            except Exception as e:
                print(f"      ⚠️ 分析失败: {e}")
    
    print(f"   ✅ 提取了 {len(type_styles)} 种类型风格")
    
    # Step 3: 按类型匹配生成
    print("\n🚀 Step 3: 按类型匹配生成")
    print("=" * 70)
    
    generated_results = []
    
    for img_type, style_info in type_styles.items():
        ref_info = style_info['reference']
        type_name = ref_info['type_name']
        
        print(f"\n🎨 生成 {type_name}")
        print("-" * 50)
        
        # 获取该类型的场景prompt
        scene_prompt = get_scene_prompt_by_type(img_type)
        
        # 融合风格 + 场景
        fused = fuse_prompt(style_info['description'], scene_prompt)
        
        try:
            # 生成
            result_paths = generate_image(
                prompt=fused,
                style_references=style_info['representative'],
                product_reference=product_image,
                aspect_ratio='3:4',
            )
            
            # 保存到输出目录
            for path in result_paths:
                new_name = f"{img_type}_{type_name}_{os.path.basename(product_image).split('.')[0]}.png"
                new_path = os.path.join(output_dir, new_name)
                shutil.copy(path, new_path)
                generated_results.append({
                    'type': img_type,
                    'type_name': type_name,
                    'path': new_path,
                    'reference': ref_info['path']
                })
                print(f"   ✅ {type_name}: {new_name}")
                
        except Exception as e:
            print(f"   ❌ {type_name}: {str(e)}")
    
    # 汇总
    print("\n" + "=" * 70)
    print("✅ 做同款生成完成！")
    print("=" * 70)
    print(f"\n📁 生成文件 ({len(generated_results)} 张):")
    for r in generated_results:
        print(f"   - {r['type_name']}: {os.path.basename(r['path'])}")
    
    print(f"\n📂 输出目录: {output_dir}")
    
    return generated_results


def main():
    """
    示例：使用 VITREGEN 参考图 + CeraVe 产品图
    """
    print("\n" + "=" * 70)
    print("💡 示例：VITREGEN 风格 → CeraVe 产品")
    print("=" * 70)
    
    # 参考图（作者上传的多张图）
    reference_images = [
        "/Users/liujianrui/Pictures/电商-测试/2/【会员U先试】维缇芮生面霜平衡霜10ml油皮敏肌尝鲜装修护舒缓-tmall.com天猫.webp",  # 主图
        "/Users/liujianrui/Pictures/电商-测试/2/【会员U先试】维缇芮生面霜平衡霜10ml油皮敏肌尝鲜装修护舒缓-tmall.com天猫 2.webp",  # 功效图
        "/Users/liujianrui/Pictures/电商-测试/2/【会员U先试】维缇芮生面霜平衡霜10ml油皮敏肌尝鲜装修护舒缓-tmall.com天猫 3.webp",  # 场景图
        "/Users/liujianrui/Pictures/电商-测试/2/【会员U先试】维缇芮生面霜平衡霜10ml油皮敏肌尝鲜装修护舒缓-tmall.com天猫 4.webp",  # 成分图
    ]
    
    # 产品图（用户上传）
    product_image = "/Users/liujianrui/Pictures/电商-测试/input/剪贴板 2026-03-15 上午 1.49.45.jpg"
    
    # 执行"做同款"
    results = do_the_same(reference_images, product_image)
    
    print("\n" + "=" * 70)
    print("🎯 核心特点:")
    print("=" * 70)
    print("   ✅ 自动识别参考图类型（主图/功效图/场景图/成分图）")
    print("   ✅ 按类型匹配生成（同类型 → 同类型）")
    print("   ✅ 保持产品一致性（CeraVe产品不变）")
    print("   ✅ 学习风格并迁移（VITREGEN风格）")


if __name__ == "__main__":
    main()
