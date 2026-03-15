#!/usr/bin/env python3
"""
生成电商图集 - 使用双参考图模式
基于 The Ordinary 风格，生成一套电商效果图
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.analyzer import analyze_images
from core.fusion import fuse_prompt
from core.generator import generate_image


def main():
    print("=" * 70)
    print("🎨 电商图集生成 - 双参考图模式")
    print("=" * 70)
    
    # Step 1: 分析 The Ordinary 风格图集
    print("\n📸 Step 1: 分析 The Ordinary 电商风格")
    style_images_dir = "/Users/liujianrui/Pictures/电商-测试"
    style_images = [
        os.path.join(style_images_dir, f) 
        for f in os.listdir(style_images_dir) 
        if f.endswith('.webp')
    ]
    style_images.sort()
    
    print(f"   找到 {len(style_images)} 张风格参考图")
    
    # 分析图集
    description, rep_indices, rep_paths = analyze_images(style_images)
    
    print(f"   ✅ 风格分析完成")
    print(f"   📋 代表图索引: {rep_indices}")
    print(f"   🖼️  代表图: {[os.path.basename(p) for p in rep_paths]}")
    
    # Step 2: 定义要生成的电商图场景
    print("\n🎯 Step 2: 定义生成场景")
    
    scenes = [
        {
            "name": "产品主图",
            "prompt": "A premium skincare product bottle on clean white background, professional product photography, minimalist aesthetic, soft diffused lighting, centered composition, sharp focus on product details, scientific and professional aesthetic"
        },
        {
            "name": "功效展示图",
            "prompt": "Skincare product with efficacy data visualization, showing whitening and brightening effects, clean infographic style, minimalist design, soft lighting, professional product photography"
        },
        {
            "name": "成分说明图",
            "prompt": "Skincare product with ingredient highlights, scientific formula visualization, clean laboratory aesthetic, minimalist design, professional product photography, soft lighting"
        },
        {
            "name": "使用场景图",
            "prompt": "Skincare product in lifestyle setting, bathroom vanity scene, clean and minimal aesthetic, soft natural lighting, professional product photography, elegant composition"
        },
        {
            "name": "品牌故事图",
            "prompt": "Skincare brand story visualization, laboratory aesthetic, scientific professionalism, clean minimalist design, soft lighting, premium brand identity"
        }
    ]
    
    print(f"   定义了 {len(scenes)} 个场景:")
    for i, scene in enumerate(scenes, 1):
        print(f"      {i}. {scene['name']}")
    
    # Step 3: 批量生成
    print("\n🚀 Step 3: 批量生成电商图集")
    print("=" * 70)
    
    generated_files = []
    
    for i, scene in enumerate(scenes, 1):
        print(f"\n🎨 生成场景 {i}/{len(scenes)}: {scene['name']}")
        print("-" * 50)
        
        # 融合风格 + 场景描述
        fused_prompt = fuse_prompt(description, scene['prompt'])
        
        print(f"   📝 Prompt: {fused_prompt[:100]}...")
        
        try:
            # 双参考图模式生成
            result_paths = generate_image(
                prompt=fused_prompt,
                style_references=rep_paths,      # 风格参考图（The Ordinary风格）
                product_reference=None,           # 无产品参考图（生成新产品）
                aspect_ratio='3:4',
            )
            
            # 重命名为场景名称
            for path in result_paths:
                new_name = f"output_{i:02d}_{scene['name'].replace(' ', '_')}.png"
                new_path = os.path.join(os.path.dirname(path), new_name)
                os.rename(path, new_path)
                generated_files.append(new_path)
                print(f"   ✅ 生成成功: {new_name}")
                
        except Exception as e:
            print(f"   ❌ 生成失败: {e}")
    
    # 汇总
    print("\n" + "=" * 70)
    print("✅ 电商图集生成完成！")
    print("=" * 70)
    print(f"\n📁 生成文件 ({len(generated_files)} 张):")
    for f in generated_files:
        print(f"   - {os.path.basename(f)}")
    
    print(f"\n📂 输出目录: {os.path.dirname(generated_files[0]) if generated_files else 'N/A'}")


if __name__ == "__main__":
    main()
