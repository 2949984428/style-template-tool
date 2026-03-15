#!/usr/bin/env python3
"""
为 CeraVe 产品生成 The Ordinary 风格的电商图集
双参考图模式：产品参考图（CeraVe）+ 风格参考图（The Ordinary）
"""

import os
import sys
import shutil

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.analyzer import analyze_images
from core.fusion import fuse_prompt
from core.generator import generate_image


def main():
    print("=" * 70)
    print("🎨 CeraVe 产品电商图集生成 - 双参考图模式")
    print("=" * 70)
    
    # Step 1: 准备产品参考图
    print("\n📸 Step 1: 准备产品参考图")
    product_ref = "/Users/liujianrui/Pictures/电商-测试/input/剪贴板 2026-03-15 上午 1.49.45.jpg"
    
    if not os.path.exists(product_ref):
        print(f"   ❌ 产品参考图不存在: {product_ref}")
        return
    
    # 复制到工作目录
    local_product = "user_cerave_product.jpg"
    shutil.copy(product_ref, local_product)
    print(f"   ✅ 产品参考图已准备好: {local_product}")
    print(f"   🧴 产品: CeraVe SA Smoothing Cleanser")
    print(f"   📋 特点: For Dry, Rough, Bumpy Skin")
    print(f"   🔬 成分: 3 Essential Ceramides, Salicylic Acid, Hyaluronic Acid")
    
    # Step 2: 分析 The Ordinary 风格
    print("\n📸 Step 2: 分析 The Ordinary 电商风格")
    style_images_dir = "/Users/liujianrui/Pictures/电商-测试"
    style_images = [
        os.path.join(style_images_dir, f) 
        for f in os.listdir(style_images_dir) 
        if f.endswith('.webp')
    ]
    style_images.sort()
    
    print(f"   找到 {len(style_images)} 张风格参考图")
    
    # 分析图集，获取风格描述 + 代表图路径
    description, rep_indices, rep_paths = analyze_images(style_images)
    
    print(f"   ✅ 风格分析完成")
    print(f"   📋 代表图索引: {rep_indices}")
    print(f"   🖼️  代表图: {[os.path.basename(p) for p in rep_paths]}")
    
    # Step 3: 定义要生成的电商图场景
    print("\n🎯 Step 3: 定义生成场景")
    
    scenes = [
        {
            "name": "产品主图",
            "prompt": "CeraVe SA Smoothing Cleanser bottle with pump, maintaining exact same product design, CeraVe logo, blue cap, and label, on clean white background, professional e-commerce product photography, minimalist aesthetic, soft diffused lighting, centered composition"
        },
        {
            "name": "功效展示图",
            "prompt": "CeraVe SA Smoothing Cleanser showcasing efficacy for dry rough bumpy skin, with exfoliates and smooths benefits, maintaining exact same bottle design with CeraVe logo and blue cap, clean infographic style, minimalist design, professional product photography"
        },
        {
            "name": "成分说明图",
            "prompt": "CeraVe SA Smoothing Cleanser highlighting Salicylic Acid, 3 Essential Ceramides and Hyaluronic Acid ingredients, maintaining exact same bottle design with CeraVe logo and blue cap, scientific formula visualization, clean laboratory aesthetic, minimalist design"
        },
        {
            "name": "使用场景图",
            "prompt": "CeraVe SA Smoothing Cleanser in bathroom lifestyle setting, on vanity with towel and skincare accessories, maintaining exact same bottle design with CeraVe logo and blue cap, clean and minimal aesthetic, soft natural lighting, professional product photography"
        },
        {
            "name": "品牌故事图",
            "prompt": "CeraVe SA Smoothing Cleanser with Developed with Dermatologists branding, laboratory background, maintaining exact same bottle design with CeraVe logo and blue cap, scientific professionalism, clean minimalist design, soft lighting, premium brand identity"
        }
    ]
    
    print(f"   定义了 {len(scenes)} 个场景:")
    for i, scene in enumerate(scenes, 1):
        print(f"      {i}. {scene['name']}")
    
    # Step 4: 批量生成（双参考图模式）
    print("\n🚀 Step 4: 批量生成电商图集（双参考图模式）")
    print("=" * 70)
    print(f"   📌 风格参考图: {len(rep_paths)} 张（The Ordinary 风格）")
    print(f"   📌 产品参考图: {local_product}（CeraVe SA Smoothing Cleanser）")
    print("=" * 70)
    
    generated_files = []
    
    for i, scene in enumerate(scenes, 1):
        print(f"\n🎨 生成场景 {i}/{len(scenes)}: {scene['name']}")
        print("-" * 50)
        
        # 融合风格 + 场景描述
        fused_prompt = fuse_prompt(description, scene['prompt'])
        
        print(f"   📝 Prompt: {fused_prompt[:80]}...")
        
        try:
            # 双参考图模式生成
            result_paths = generate_image(
                prompt=fused_prompt,
                style_references=rep_paths,           # 风格参考图（The Ordinary风格）
                product_reference=local_product,       # 产品参考图（CeraVe产品）
                aspect_ratio='3:4',
            )
            
            # 重命名为场景名称
            for path in result_paths:
                new_name = f"cerave_{i:02d}_{scene['name'].replace(' ', '_')}.png"
                new_path = os.path.join(os.path.dirname(path), new_name)
                os.rename(path, new_path)
                generated_files.append(new_path)
                print(f"   ✅ 生成成功: {new_name}")
                
        except Exception as e:
            print(f"   ❌ 生成失败: {e}")
            import traceback
            traceback.print_exc()
    
    # 汇总
    print("\n" + "=" * 70)
    print("✅ CeraVe 电商图集生成完成！")
    print("=" * 70)
    print(f"\n📁 生成文件 ({len(generated_files)} 张):")
    for f in generated_files:
        print(f"   - {os.path.basename(f)}")
    
    print(f"\n📂 输出目录: {os.path.dirname(generated_files[0]) if generated_files else 'N/A'}")
    
    print("\n🎯 双参考图模式效果:")
    print("   ✅ 保持 CeraVe 产品不变（瓶身、标签、Logo）")
    print("   ✅ 应用 The Ordinary 风格（背景、光影、排版）")
    print("   ✅ 生成专业电商效果图")


if __name__ == "__main__":
    main()
