#!/usr/bin/env python3
"""
图像类型分类器
自动识别电商图片的类型
"""

from google import genai
from google.genai import types
import config

# 图像类型定义
IMAGE_TYPES = {
    "main": {
        "name": "主图",
        "keywords": ["产品主图", "单品展示", "白底产品", "product shot", "hero image"],
        "description": "产品主体展示，通常是白底或简洁背景"
    },
    "efficacy": {
        "name": "功效图",
        "keywords": ["功效展示", "效果对比", "数据可视化", "before after", "clinical results"],
        "description": "展示产品功效、效果数据、前后对比"
    },
    "ingredient": {
        "name": "成分图",
        "keywords": ["成分说明", "配方展示", "科技成分", "分子结构", "ingredients"],
        "description": "展示产品成分、配方科技、原料来源"
    },
    "scene": {
        "name": "场景图",
        "keywords": ["使用场景", "生活场景", "模特展示", "lifestyle", "usage scenario"],
        "description": "展示产品使用场景、生活方式、真人使用"
    },
    "brand": {
        "name": "品牌图",
        "keywords": ["品牌故事", "品牌介绍", "实验室", "研发背景", "brand story"],
        "description": "展示品牌故事、研发背景、权威认证"
    }
}


def classify_image(image_path):
    """
    使用 Gemini 多模态模型识别图像类型
    
    Args:
        image_path: 图片路径
        
    Returns:
        (image_type, type_name, confidence)
        image_type: main/efficacy/ingredient/scene/brand
        type_name: 中文名称
        confidence: 置信度
    """
    client = genai.Client(api_key=config.GEMINI_API_KEY)
    
    # 读取图片
    with open(image_path, "rb") as f:
        image_data = f.read()
    
    # 构建提示词
    type_descriptions = "\n".join([
        f"- {key}: {info['name']} - {info['description']}"
        for key, info in IMAGE_TYPES.items()
    ])
    
    prompt = f"""分析这张电商图片的类型。请选择最符合的类型：

可选类型：
{type_descriptions}

请回答格式：类型|置信度(0-100)|原因
例如：main|95|这是产品主图，白底展示产品主体"""

    # 调用 Gemini
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=[
            types.Part.from_text(text=prompt),
            types.Part.from_bytes(data=image_data, mime_type="image/jpeg")
        ],
        config=types.GenerateContentConfig(max_output_tokens=100)
    )
    
    # 解析结果
    result_text = response.text.strip()
    
    try:
        parts = result_text.split("|")
        image_type = parts[0].strip().lower()
        confidence = int(parts[1].strip())
        
        # 标准化类型名称
        type_mapping = {
            "main": "main",
            "主图": "main",
            "efficacy": "efficacy",
            "功效": "efficacy",
            "功效图": "efficacy",
            "ingredient": "ingredient",
            "成分": "ingredient",
            "成分图": "ingredient",
            "scene": "scene",
            "场景": "scene",
            "场景图": "scene",
            "brand": "brand",
            "品牌": "brand",
            "品牌图": "brand"
        }
        
        normalized_type = type_mapping.get(image_type, "main")
        type_name = IMAGE_TYPES[normalized_type]["name"]
        
        return normalized_type, type_name, confidence
        
    except Exception as e:
        # 解析失败，返回默认值
        return "main", "主图", 50


def get_scene_prompt_by_type(image_type):
    """
    根据图像类型获取对应的场景prompt
    
    Args:
        image_type: main/efficacy/ingredient/scene/brand
        
    Returns:
        场景描述prompt
    """
    prompts = {
        "main": "product photography on clean background, professional e-commerce style, minimalist aesthetic, centered composition, sharp focus on product details",
        
        "efficacy": "product efficacy showcase with data visualization, clinical results display, percentage data, before after comparison, clean infographic style, professional medical aesthetic",
        
        "ingredient": "scientific formula visualization, ingredient highlights, laboratory aesthetic, molecular structure display, clean technical design, ingredient sourcing",
        
        "scene": "lifestyle product photography, usage scenario, model holding product, natural lighting, bathroom or vanity setting, authentic usage moment",
        
        "brand": "brand story visualization, laboratory background, research and development scene, authoritative certification, scientific professionalism, brand heritage"
    }
    
    return prompts.get(image_type, prompts["main"])


def analyze_uploaded_set(image_paths):
    """
    分析用户上传的一套图片，识别每张图的类型
    
    Args:
        image_paths: 图片路径列表
        
    Returns:
        [(image_path, image_type, type_name, is_main), ...]
    """
    results = []
    
    for i, path in enumerate(image_paths):
        img_type, type_name, confidence = classify_image(path)
        
        # 第一张默认为主图（如果识别置信度不够高）
        is_main = (i == 0) or (img_type == "main" and confidence > 80)
        
        results.append({
            "path": path,
            "type": img_type,
            "type_name": type_name,
            "confidence": confidence,
            "is_main": is_main
        })
    
    return results


if __name__ == "__main__":
    # 测试
    import sys
    if len(sys.argv) > 1:
        test_image = sys.argv[1]
        img_type, type_name, confidence = classify_image(test_image)
        print(f"图片: {test_image}")
        print(f"类型: {type_name} ({img_type})")
        print(f"置信度: {confidence}%")
