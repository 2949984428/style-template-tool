#!/usr/bin/env python3
"""
使用 VITREGEN 风格生成电商图集
风格参考图: VITREGEN 维缇芮生面霜
产品参考图: 用户电商图
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
    print("🎨 VITREGEN 风格电商图集生成")
    print("=" * 70)
    
    # Step 1: 分析 VITREGEN 风格
    print("\n📸 Step 1: 分析 VITREGEN 风格图集")
    style_images_dir = "/Users/liujianrui/Pictures/电商-测试/2"
    style_images = [
        os.path.join(style_images_dir, f) 
        for f in os.listdir(style_images_dir) 
        if f.endswith('.webp')
    ]
    style_images.sort()
    
    print(f"   找到 {len(style_images)} 张 VITREGEN 风格参考图")
    
    # 分析图集
    description, rep_indices, rep_paths = analyze_images(style_images)
    
    print(f"   ✅ 风格分析完成")
    print(f"   📋 代表图索引: {rep_indices}")
    print(f"   🖼️  代表图: {[os.path.basename(p) for p in rep_paths]}")
    
    # Step 2: 准备产品参考图
    print("\n📸 Step 2: 准备产品参考图")
    # 用户电商图路径（请根据实际情况修改）
    product_ref = "/Users/liujianrui/Pictures/电商-测试/input/剪贴板 2026-03-15 上午 1.49.45.jpg"
    
    if not os.path.exists(product_ref):
        print(f"   ⚠️  产品参考图不存在，将仅使用风格参考生成")
        product_ref = None
    else:
        print(f"   ✅ 产品参考图: {os.path.basename(product_ref)}")
    
    # Step 3: 定义 VITREGEN 风格场景
    print("\n🎯 Step 3: 定义生成场景")
    
    scenes = [
        {
            "name": "功效展示图",
            "prompt": "product photography with efficacy data visualization, warm beige background, model holding product, professional clinical results display, percentage data, 28-day results promise, authoritative certification, clean minimalist design"
        },
        {
            "name": "产品主图",
            "prompt": "product photography on warm beige background, professional e-commerce style, soft natural lighting, clean composition, premium skincare aesthetic, minimalist design"
        },
        {
            "name": "成分科技图",
            "prompt": "scientific formula visualization, ingredient highlights, laboratory aesthetic, warm tone background, professional product photography, skin barrier technology"
        },
        {
            "name": "使用场景图",
            "prompt": "lifestyle product photography, bathroom vanity setting, warm natural lighting, clean aesthetic, model hands holding product, premium skincare routine"
        },
        {
            "name": "品牌信任图",
            "prompt": "brand trust visualization, authoritative certification badges, clinical study results, warm beige background, professional medical aesthetic, dermatologist approved"
        },
    ]
    
    print(f"   定义了 {len(scenes)} 个场景")
    
    # Step 4: 批量生成
    print("\n🚀 Step 4: 批量生成 VITREGEN 风格电商图")
    print("=" * 70)
    
    generated_files = []
    logs = []
    
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
                new_name = f"vitregen_{i:02d}_{scene['name']}.png"
                new_path = os.path.join(os.path.dirname(path), new_name)
                shutil.move(path, new_path)
                generated_files.append(new_path)
                print(f"   ✅ {scene['name']}: {new_name}")
                
        except Exception as e:
            print(f"   ❌ {scene['name']}: {str(e)}")
    
    # 汇总
    print("\n" + "=" * 70)
    print("✅ VITREGEN 风格电商图集生成完成！")
    print("=" * 70)
    print(f"\n📁 生成文件 ({len(generated_files)} 张):")
    for f in generated_files:
        print(f"   - {os.path.basename(f)}")
    
    print("\n🎯 风格特点:")
    print("   ✅ 暖色调背景（米黄色）")
    print("   ✅ 功效数据可视化")
    print("   ✅ 28天效果承诺")
    print("   ✅ 权威机构认证风格")
    print("   ✅ 专业医学美学")


if __name__ == "__main__":
    main()
