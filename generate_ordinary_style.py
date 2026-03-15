#!/usr/bin/env python3
"""
使用 The Ordinary 风格生成 CeraVe 电商图
参考图: /Users/liujianrui/Pictures/电商-测试/1/
产品图: CeraVe SA Smoothing Cleanser
"""

import os
import sys
import shutil

sys.path.insert(0, os.path.dirname(__file__))

from core.analyzer import analyze_images
from core.fusion import fuse_prompt
from core.generator import generate_image


def main():
    print("=" * 70)
    print("🎨 The Ordinary 风格电商图生成")
    print("=" * 70)
    
    # Step 1: 分析 The Ordinary 风格
    print("\n📸 Step 1: 分析 The Ordinary 风格图集")
    style_images_dir = "/Users/liujianrui/Pictures/电商-测试/1"
    style_images = [
        os.path.join(style_images_dir, f) 
        for f in os.listdir(style_images_dir) 
        if f.endswith('.webp')
    ]
    style_images.sort()
    
    print(f"   找到 {len(style_images)} 张 The Ordinary 风格参考图")
    
    # 分析图集
    description, rep_indices, rep_paths = analyze_images(style_images)
    
    print(f"   ✅ 风格分析完成")
    print(f"   📋 代表图索引: {rep_indices}")
    print(f"   🖼️  代表图: {[os.path.basename(p) for p in rep_paths]}")
    
    # Step 2: 准备产品参考图
    print("\n📸 Step 2: 准备产品参考图")
    product_ref = "/Users/liujianrui/Pictures/电商-测试/input/剪贴板 2026-03-15 上午 1.49.45.jpg"
    
    if not os.path.exists(product_ref):
        print(f"   ⚠️  产品参考图不存在")
        product_ref = None
    else:
        print(f"   ✅ 产品参考图: CeraVe SA Smoothing Cleanser")
    
    # Step 3: 定义 The Ordinary 风格场景
    print("\n🎯 Step 3: 定义生成场景")
    
    scenes = [
        {
            "name": "品牌故事图",
            "prompt": "brand story visualization, minimalist white background, large typography headline, laboratory scene, scientific professionalism, clean modern design, 'Hello China' style branding"
        },
        {
            "name": "产品主图",
            "prompt": "product photography on clean white background, minimalist aesthetic, The Ordinary style, scientific skincare presentation, simple composition, professional lighting"
        },
        {
            "name": "成分科技图",
            "prompt": "ingredient science visualization, laboratory equipment, molecular structures, clean white background, scientific formula presentation, The Ordinary aesthetic"
        },
        {
            "name": "功效说明图",
            "prompt": "efficacy explanation with clean typography, minimalist design, percentage data display, scientific results, white background, simple icons"
        },
        {
            "name": "实验室场景图",
            "prompt": "laboratory setting with scientist, modern lab equipment, clean white environment, scientific research atmosphere, professional skincare development"
        },
    ]
    
    print(f"   定义了 {len(scenes)} 个场景")
    
    # Step 4: 批量生成
    print("\n🚀 Step 4: 批量生成 The Ordinary 风格电商图")
    print("=" * 70)
    
    generated_files = []
    
    for i, scene in enumerate(scenes, 1):
        print(f"\n🎨 生成场景 {i}/{len(scenes)}: {scene['name']}")
        print("-" * 50)
        
        # 融合风格 + 场景
        fused = fuse_prompt(description, scene['prompt'])
        
        try:
            result_paths = generate_image(
                prompt=fused,
                style_references=rep_paths,
                product_reference=product_ref,
                aspect_ratio='3:4',
            )
            
            # 重命名
            for path in result_paths:
                new_name = f"ordinary_{i:02d}_{scene['name']}.png"
                new_path = os.path.join(os.path.dirname(path), new_name)
                shutil.move(path, new_path)
                generated_files.append(new_path)
                print(f"   ✅ {scene['name']}: {new_name}")
                
        except Exception as e:
            print(f"   ❌ {scene['name']}: {e}")
    
    # 汇总
    print("\n" + "=" * 70)
    print("✅ The Ordinary 风格电商图生成完成！")
    print("=" * 70)
    print(f"\n📁 生成文件 ({len(generated_files)} 张):")
    for f in generated_files:
        print(f"   - {os.path.basename(f)}")
    
    print("\n🎯 The Ordinary 风格特点:")
    print("   ✅ 极简白色背景")
    print("   ✅ 大字体标题")
    print("   ✅ 实验室场景")
    print("   ✅ 科学专业感")
    print("   ✅ 品牌故事叙述")


if __name__ == "__main__":
    main()
