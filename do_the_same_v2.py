#!/usr/bin/env python3
"""
"做同款" V2 - 支持全类型设计
电商图、Logo、Branding Kit、海报等
"""

import os
import sys
import shutil

sys.path.insert(0, os.path.dirname(__file__))

from core.design_classifier import classify_design_image, get_generation_prompt, DESIGN_CATEGORIES
from core.analyzer import analyze_images
from core.fusion import fuse_prompt
from core.generator import generate_image


def do_the_same_v2(reference_images, user_content=None, output_dir="outputs/do_the_same_v2"):
    """
    做同款 V2 - 智能识别设计类型并生成
    
    Args:
        reference_images: 参考图路径列表（支持混合类型：电商图+Logo+海报等）
        user_content: 用户上传的内容（产品图/品牌名/文案等）
        output_dir: 输出目录
        
    Returns:
        生成结果列表
    """
    print("=" * 70)
    print("🎨 做同款 V2 - 全类型设计生成")
    print("=" * 70)
    
    os.makedirs(output_dir, exist_ok=True)
    
    # Step 1: 智能识别每张参考图的类型
    print("\n📸 Step 1: 智能识别设计类型")
    
    design_analysis = []
    for i, img_path in enumerate(reference_images, 1):
        print(f"\n   分析第 {i} 张图: {os.path.basename(img_path)}")
        
        try:
            design_info = classify_design_image(img_path)
            design_analysis.append({
                "path": img_path,
                "info": design_info
            })
            
            print(f"      大类: {design_info['category_name']}")
            print(f"      类型: {design_info['type_name']}")
            print(f"      风格: {design_info['style_features']['style']}")
            print(f"      情绪: {design_info['style_features']['mood']}")
            
        except Exception as e:
            print(f"      ⚠️ 分析失败: {e}")
    
    print(f"\n   ✅ 共识别 {len(design_analysis)} 张参考图")
    
    # Step 2: 按类型分组
    print("\n📸 Step 2: 按设计类型分组")
    
    type_groups = {}
    for item in design_analysis:
        key = (item['info']['category'], item['info']['type'])
        if key not in type_groups:
            type_groups[key] = {
                'category_name': item['info']['category_name'],
                'type_name': item['info']['type_name'],
                'images': [],
                'style_features': item['info']['style_features']
            }
        type_groups[key]['images'].append(item['path'])
    
    for (cat, typ), group in type_groups.items():
        print(f"   {group['category_name']} - {group['type_name']}: {len(group['images'])} 张")
    
    # Step 3: 按类型提取风格并生成
    print("\n🚀 Step 3: 按类型匹配生成")
    print("=" * 70)
    
    generated_results = []
    
    for (category, design_type), group in type_groups.items():
        print(f"\n🎨 生成 {group['category_name']} - {group['type_name']}")
        print("-" * 50)
        
        # 提取该类型的风格
        try:
            print("   提取风格...")
            desc, _, rep_paths = analyze_images(group['images'])
            
            # 获取该类型的生成prompt
            sample_info = {
                'prompt_template': DESIGN_CATEGORIES[category]['types'][design_type]['prompt'],
                'style_features': group['style_features']
            }
            base_prompt = get_generation_prompt(sample_info)
            
            # 融合风格 + 类型prompt
            fused = fuse_prompt(desc, base_prompt)
            
            # 生成
            print("   生成图片...")
            result_paths = generate_image(
                prompt=fused,
                style_references=rep_paths,
                product_reference=user_content,
                aspect_ratio='1:1' if category == 'branding' else '3:4',
            )
            
            # 保存
            for path in result_paths:
                new_name = f"{category}_{design_type}_{len(generated_results)+1:02d}.png"
                new_path = os.path.join(output_dir, new_name)
                shutil.copy(path, new_path)
                
                generated_results.append({
                    'category': category,
                    'category_name': group['category_name'],
                    'type': design_type,
                    'type_name': group['type_name'],
                    'path': new_path,
                    'style': group['style_features']
                })
                
                print(f"   ✅ {new_name}")
                
        except Exception as e:
            print(f"   ❌ 生成失败: {e}")
    
    # 汇总
    print("\n" + "=" * 70)
    print("✅ 做同款 V2 生成完成！")
    print("=" * 70)
    
    # 按类型分组展示
    from collections import defaultdict
    by_category = defaultdict(list)
    for r in generated_results:
        by_category[r['category_name']].append(r)
    
    print(f"\n📁 生成结果 ({len(generated_results)} 张):")
    for cat_name, items in by_category.items():
        print(f"\n   【{cat_name}】")
        for item in items:
            print(f"      - {item['type_name']}: {os.path.basename(item['path'])}")
    
    print(f"\n📂 输出目录: {output_dir}")
    
    return generated_results


def main():
    """
    示例：混合类型参考图生成
    """
    print("\n" + "=" * 70)
    print("💡 示例：混合类型参考图")
    print("=" * 70)
    
    # 模拟混合类型的参考图
    # 实际使用时，用户可能上传：
    # - 1张电商主图
    # - 1张Logo设计
    # - 1张海报设计
    
    # 这里先用 VITREGEN 的图作为示例
    reference_images = [
        "/Users/liujianrui/Pictures/电商-测试/2/【会员U先试】维缇芮生面霜平衡霜10ml油皮敏肌尝鲜装修护舒缓-tmall.com天猫.webp",
        "/Users/liujianrui/Pictures/电商-测试/2/【会员U先试】维缇芮生面霜平衡霜10ml油皮敏肌尝鲜装修护舒缓-tmall.com天猫 2.webp",
        "/Users/liujianrui/Pictures/电商-测试/2/【会员U先试】维缇芮生面霜平衡霜10ml油皮敏肌尝鲜装修护舒缓-tmall.com天猫 3.webp",
    ]
    
    # 用户内容（产品图/品牌素材）
    user_content = "/Users/liujianrui/Pictures/电商-测试/input/剪贴板 2026-03-15 上午 1.49.45.jpg"
    
    # 执行"做同款"
    results = do_the_same_v2(reference_images, user_content)
    
    print("\n" + "=" * 70)
    print("🎯 V2 核心特点:")
    print("=" * 70)
    print("   ✅ 自动识别设计大类（电商/品牌/营销/UI）")
    print("   ✅ 自动识别具体类型（主图/Logo/海报等）")
    print("   ✅ 识别风格特征（极简/复古/科技/自然）")
    print("   ✅ 按类型匹配生成（同类型→同类型）")
    print("   ✅ 支持混合类型参考图")
    print("   ✅ 支持Logo、Branding Kit、海报等")


if __name__ == "__main__":
    main()
