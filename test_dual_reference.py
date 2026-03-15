#!/usr/bin/env python3
"""
双参考图模式测试脚本
演示：风格参考图（来自模板）+ 产品参考图（用户上传）
"""

import os
import sys

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.analyzer import analyze_images
from core.fusion import fuse_prompt
from core.generator import generate_image


def test_dual_reference_mode():
    """测试双参考图模式"""
    
    print("=" * 60)
    print("🎨 双参考图模式测试")
    print("=" * 60)
    
    # Step 1: 分析风格图集（The Ordinary 电商图）
    print("\n📸 Step 1: 分析风格图集")
    style_images_dir = "test-images"
    style_images = [
        os.path.join(style_images_dir, f) 
        for f in os.listdir(style_images_dir) 
        if f.endswith('.webp')
    ]
    style_images.sort()
    
    print(f"   找到 {len(style_images)} 张风格参考图")
    
    # 分析图集，获取风格描述 + 代表图路径
    description, rep_indices, rep_paths = analyze_images(style_images)
    
    print(f"   ✅ 分析完成")
    print(f"   📋 代表图索引: {rep_indices}")
    print(f"   🖼️  代表图路径: {[os.path.basename(p) for p in rep_paths]}")
    
    # Step 2: 融合用户输入
    print("\n🔄 Step 2: Prompt 融合")
    user_prompt = "CeraVe SA Smoothing Cleanser 洁面产品，专业电商风格"
    
    fused_prompt = fuse_prompt(description, user_prompt)
    print(f"   ✅ 融合完成")
    print(f"   📝 融合后 Prompt 长度: {len(fused_prompt)} 字符")
    
    # Step 3: 双参考图生成
    print("\n🎨 Step 3: 双参考图生成")
    print("   📌 风格参考图（来自模板）:")
    for i, path in enumerate(rep_paths, 1):
        print(f"      {i}. {os.path.basename(path)}")
    
    product_ref = "user_ref.jpg"  # 用户提供的产品图
    print(f"   📌 产品参考图（用户上传）: {product_ref}")
    
    # 检查文件是否存在
    if not os.path.exists(product_ref):
        print(f"   ⚠️  {product_ref} 不存在，跳过产品参考图")
        product_ref = None
    
    print("\n   🚀 开始生成...")
    
    try:
        result_paths = generate_image(
            prompt=fused_prompt,
            style_references=rep_paths,      # 风格参考图（来自模板）
            product_reference=product_ref,    # 产品参考图（用户上传）
            aspect_ratio='3:4',
        )
        
        print(f"   ✅ 生成完成！")
        print(f"   📁 生成结果:")
        for path in result_paths:
            print(f"      - {path}")
            
    except Exception as e:
        print(f"   ❌ 生成失败: {e}")
        import traceback
        traceback.print_exc()


def test_style_only_mode():
    """测试仅风格参考图模式（无产品参考图）"""
    
    print("\n" + "=" * 60)
    print("🎨 仅风格参考图模式测试")
    print("=" * 60)
    
    # 使用之前的分析结果
    style_images_dir = "test-images"
    style_images = [
        os.path.join(style_images_dir, f) 
        for f in os.listdir(style_images_dir) 
        if f.endswith('.webp')
    ]
    style_images.sort()
    
    description, rep_indices, rep_paths = analyze_images(style_images)
    
    user_prompt = "一款高端护肤品，极简风格，白色背景"
    fused_prompt = fuse_prompt(description, user_prompt)
    
    print("\n   🚀 开始生成（仅风格参考，无产品参考）...")
    
    try:
        result_paths = generate_image(
            prompt=fused_prompt,
            style_references=rep_paths,      # 仅风格参考图
            product_reference=None,           # 无产品参考图
            aspect_ratio='3:4',
        )
        
        print(f"   ✅ 生成完成！")
        print(f"   📁 生成结果:")
        for path in result_paths:
            print(f"      - {path}")
            
    except Exception as e:
        print(f"   ❌ 生成失败: {e}")


if __name__ == "__main__":
    # 测试双参考图模式
    test_dual_reference_mode()
    
    # 测试仅风格参考图模式
    test_style_only_mode()
    
    print("\n" + "=" * 60)
    print("✅ 所有测试完成！")
    print("=" * 60)
