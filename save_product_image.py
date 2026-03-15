#!/usr/bin/env python3
"""
保存用户提供的产品图
"""

import os
import sys

def save_base64_image(base64_data, output_path="user_cerave_product.jpg"):
    """保存 base64 编码的图片"""
    try:
        # 移除可能的 data URL 前缀
        if ',' in base64_data:
            base64_data = base64_data.split(',')[1]
        
        # 解码并保存
        import base64
        image_data = base64.b64decode(base64_data)
        
        with open(output_path, 'wb') as f:
            f.write(image_data)
        
        print(f"✅ 产品图已保存: {output_path}")
        print(f"   文件大小: {len(image_data)} bytes")
        return True
        
    except Exception as e:
        print(f"❌ 保存失败: {e}")
        return False


if __name__ == "__main__":
    # 检查命令行参数
    if len(sys.argv) < 2:
        print("用法: python3 save_product_image.py <base64_image_data>")
        print("或: python3 save_product_image.py --file <image_file_path>")
        sys.exit(1)
    
    if sys.argv[1] == '--file':
        # 从文件复制
        import shutil
        src = sys.argv[2]
        dst = "user_cerave_product.jpg"
        shutil.copy(src, dst)
        print(f"✅ 产品图已复制: {src} -> {dst}")
    else:
        # 从 base64 保存
        base64_data = sys.argv[1]
        save_base64_image(base64_data)
