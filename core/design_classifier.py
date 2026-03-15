#!/usr/bin/env python3
"""
设计图像分类器 - 扩展版
支持：电商图、Logo、Branding Kit、海报等多种设计类型
"""

from google import genai
from google.genai import types
import config

# 完整的设计类型体系
DESIGN_CATEGORIES = {
    "ecommerce": {
        "name": "电商设计",
        "types": {
            "main": {"name": "电商主图", "prompt": "product photography on clean background"},
            "efficacy": {"name": "功效展示", "prompt": "efficacy showcase with data visualization"},
            "ingredient": {"name": "成分说明", "prompt": "scientific formula visualization"},
            "scene": {"name": "使用场景", "prompt": "lifestyle product photography"},
            "brand": {"name": "品牌故事", "prompt": "brand story visualization"}
        }
    },
    
    "branding": {
        "name": "品牌设计",
        "types": {
            "logo_symbol": {"name": "Logo图形标", "prompt": "logo symbol design, iconic mark, simple geometric shape"},
            "logo_wordmark": {"name": "Logo文字标", "prompt": "wordmark logo design, typography-based logo"},
            "logo_combination": {"name": "组合Logo", "prompt": "combination logo with symbol and wordmark"},
            "brand_guidelines": {"name": "品牌规范", "prompt": "brand guidelines document, usage examples"},
            "brand_colors": {"name": "品牌色板", "prompt": "brand color palette, color system"},
            "brand_typography": {"name": "品牌字体", "prompt": "brand typography system, font pairing"},
            "brand_messaging": {"name": "品牌语言", "prompt": "brand messaging, tone of voice"}
        }
    },
    
    "marketing": {
        "name": "营销物料",
        "types": {
            "poster": {"name": "海报设计", "prompt": "poster design, promotional graphic"},
            "social_media": {"name": "社交媒体图", "prompt": "social media post, Instagram/Facebook graphic"},
            "banner": {"name": "Banner横幅", "prompt": "web banner, header graphic"},
            "flyer": {"name": "宣传单页", "prompt": "flyer design, single page promotion"},
            "brochure": {"name": "宣传册", "prompt": "brochure design, multi-page layout"},
            "packaging": {"name": "包装设计", "prompt": "product packaging design"},
            "merchandise": {"name": "周边物料", "prompt": "merchandise design, branded items"}
        }
    },
    
    "uiux": {
        "name": "UI/UX设计",
        "types": {
            "app_icon": {"name": "App图标", "prompt": "app icon design, mobile application icon"},
            "web_design": {"name": "网页设计", "prompt": "web design, website layout"},
            "mobile_ui": {"name": "移动端界面", "prompt": "mobile UI design, smartphone interface"},
            "dashboard": {"name": "数据仪表盘", "prompt": "dashboard design, data visualization interface"},
            "landing_page": {"name": "落地页", "prompt": "landing page design, conversion-focused page"}
        }
    }
}


def recognize_category(image_path):
    """
    识别设计图像的大类
    
    Returns:
        category: "ecommerce" | "branding" | "marketing" | "uiux"
    """
    client = genai.Client(api_key=config.GEMINI_API_KEY)
    
    with open(image_path, "rb") as f:
        image_data = f.read()
    
    prompt = """分析这张设计图片的类型大类。请选择最符合的类别：

可选类别：
1. ecommerce - 电商设计（产品展示、商品详情页、电商主图）
2. branding - 品牌设计（Logo、品牌色板、品牌字体、VI规范）
3. marketing - 营销物料（海报、传单、社交媒体图、Banner）
4. uiux - UI/UX设计（App界面、网页设计、图标、仪表盘）

请只回答类别名称（小写），例如：ecommerce"""

    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=[
            types.Part.from_text(text=prompt),
            types.Part.from_bytes(data=image_data, mime_type="image/jpeg")
        ],
        config=types.GenerateContentConfig(max_output_tokens=50)
    )
    
    result = response.text.strip().lower()
    
    # 标准化
    category_map = {
        "ecommerce": "ecommerce",
        "电商": "ecommerce",
        "branding": "branding",
        "品牌": "branding",
        "marketing": "marketing",
        "营销": "marketing",
        "uiux": "uiux",
        "ui": "uiux",
        "ux": "uiux",
        "界面": "uiux"
    }
    
    return category_map.get(result, "ecommerce")


def recognize_specific_type(image_path, category):
    """
    识别具体的设计类型
    
    Args:
        image_path: 图片路径
        category: 大类（ecommerce/branding/marketing/uiux）
    
    Returns:
        specific_type: 具体类型代码
    """
    client = genai.Client(api_key=config.GEMINI_API_KEY)
    
    with open(image_path, "rb") as f:
        image_data = f.read()
    
    # 根据大类构建提示词
    if category == "ecommerce":
        options = """main（产品主图）、efficacy（功效展示）、ingredient（成分说明）、scene（使用场景）、brand（品牌故事）"""
    elif category == "branding":
        options = """logo_symbol（Logo图形标）、logo_wordmark（Logo文字标）、logo_combination（组合Logo）、brand_guidelines（品牌规范）、brand_colors（品牌色板）、brand_typography（品牌字体）"""
    elif category == "marketing":
        options = """poster（海报）、social_media（社交媒体图）、banner（Banner横幅）、flyer（传单）、brochure（宣传册）、packaging（包装）"""
    elif category == "uiux":
        options = """app_icon（App图标）、web_design（网页设计）、mobile_ui（移动端界面）、dashboard（仪表盘）、landing_page（落地页）"""
    else:
        options = "main"
    
    prompt = f"""分析这张{type}设计图片的具体类型。

可选类型：
{options}

请只回答类型代码（小写），例如：logo_symbol"""

    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=[
            types.Part.from_text(text=prompt),
            types.Part.from_bytes(data=image_data, mime_type="image/jpeg")
        ],
        config=types.GenerateContentConfig(max_output_tokens=50)
    )
    
    result = response.text.strip().lower()
    
    # 验证结果是否在有效类型中
    valid_types = DESIGN_CATEGORIES.get(category, {}).get("types", {})
    if result in valid_types:
        return result
    
    # 返回默认类型
    return list(valid_types.keys())[0] if valid_types else "main"


def recognize_style_features(image_path):
    """
    识别设计风格特征
    
    Returns:
        {
            "style": "minimalist" | "vintage" | "tech" | "natural" | "luxury" | "playful",
            "color_temperature": "warm" | "cool" | "neutral",
            "complexity": "simple" | "moderate" | "complex",
            "mood": "professional" | "friendly" | "elegant" | "energetic"
        }
    """
    client = genai.Client(api_key=config.GEMINI_API_KEY)
    
    with open(image_path, "rb") as f:
        image_data = f.read()
    
    prompt = """分析这张设计图的风格特征，请用以下格式回答：

风格类型: [minimalist/vintage/tech/natural/luxury/playful]
色温: [warm/cool/neutral]
复杂度: [simple/moderate/complex]
情绪: [professional/friendly/elegant/energetic]

例如：
风格类型: minimalist
色温: cool
复杂度: simple
情绪: professional"""

    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=[
            types.Part.from_text(text=prompt),
            types.Part.from_bytes(data=image_data, mime_type="image/jpeg")
        ],
        config=types.GenerateContentConfig(max_output_tokens=100)
    )
    
    result_text = response.text.strip()
    
    # 解析结果
    features = {
        "style": "minimalist",
        "color_temperature": "neutral",
        "complexity": "moderate",
        "mood": "professional"
    }
    
    for line in result_text.split("\n"):
        if ":" in line:
            key, value = line.split(":", 1)
            key = key.strip()
            value = value.strip()
            
            if "风格" in key or "style" in key.lower():
                features["style"] = value
            elif "色温" in key or "temperature" in key.lower():
                features["color_temperature"] = value
            elif "复杂度" in key or "complexity" in key.lower():
                features["complexity"] = value
            elif "情绪" in key or "mood" in key.lower():
                features["mood"] = value
    
    return features


def classify_design_image(image_path):
    """
    完整的设计图像分类
    
    Returns:
        {
            "category": "branding",
            "category_name": "品牌设计",
            "type": "logo_symbol",
            "type_name": "Logo图形标",
            "prompt_template": "logo symbol design...",
            "style_features": {...},
            "confidence": 95
        }
    """
    # 第一层：识别大类
    category = recognize_category(image_path)
    category_info = DESIGN_CATEGORIES.get(category, {})
    category_name = category_info.get("name", "未知")
    
    # 第二层：识别具体类型
    specific_type = recognize_specific_type(image_path, category)
    type_info = category_info.get("types", {}).get(specific_type, {})
    type_name = type_info.get("name", "未知")
    prompt_template = type_info.get("prompt", "")
    
    # 第三层：识别风格特征
    style_features = recognize_style_features(image_path)
    
    return {
        "category": category,
        "category_name": category_name,
        "type": specific_type,
        "type_name": type_name,
        "prompt_template": prompt_template,
        "style_features": style_features,
        "confidence": 90  # 可以基于多模态分析的置信度
    }


def get_generation_prompt(design_info, user_requirements=None):
    """
    根据设计信息生成完整的生图prompt
    
    Args:
        design_info: classify_design_image的返回结果
        user_requirements: 用户的额外要求
    
    Returns:
        完整的生图prompt
    """
    base_prompt = design_info["prompt_template"]
    style = design_info["style_features"]
    
    # 构建风格描述
    style_desc = f"""{style['style']} design style, 
{style['color_temperature']} color temperature, 
{style['complexity']} complexity, 
{style['mood']} mood"""
    
    # 合并基础prompt和风格
    full_prompt = f"{base_prompt}, {style_desc}"
    
    # 添加用户要求
    if user_requirements:
        full_prompt += f", {user_requirements}"
    
    return full_prompt


if __name__ == "__main__":
    # 测试
    import sys
    if len(sys.argv) > 1:
        test_image = sys.argv[1]
        result = classify_design_image(test_image)
        
        print(f"图片: {test_image}")
        print(f"大类: {result['category_name']} ({result['category']})")
        print(f"类型: {result['type_name']} ({result['type']})")
        print(f"风格: {result['style_features']}")
        print(f"Prompt模板: {result['prompt_template']}")
