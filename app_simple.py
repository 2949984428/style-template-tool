"""
风格模板自动化工具 - 简化版 Gradio UI
支持：双参考图模式 + 批量生成套图
"""

import os
import sys
import gradio as gr
import shutil
from datetime import datetime

sys.path.insert(0, os.path.dirname(__file__))

import config
from core.analyzer import analyze_images
from core.fusion import fuse_prompt
from core.generator import generate_image

# 全局状态
state = {
    "template_description": "",
    "representative_paths": [],
    "all_image_paths": [],
}

# 电商场景预设
SCENES = [
    ("产品主图", "product photography on clean white background, professional e-commerce style"),
    ("功效展示图", "showcasing efficacy and benefits, with data visualization"),
    ("成分说明图", "highlighting ingredients, scientific formula visualization"),
    ("使用场景图", "in lifestyle setting, bathroom vanity scene"),
    ("品牌故事图", "brand story visualization, laboratory background"),
]


def analyze_style(images):
    """分析风格"""
    if not images:
        return "请先上传图片", []
    
    try:
        description, rep_indices, rep_paths = analyze_images(images)
        state["template_description"] = description
        state["representative_paths"] = rep_paths
        state["all_image_paths"] = images
        return description, rep_paths
    except Exception as e:
        return f"分析失败: {str(e)}", []


def fuse(user_prompt):
    """融合 prompt"""
    if not state["template_description"]:
        return "请先分析风格"
    if not user_prompt:
        return "请输入用户 prompt"
    
    try:
        fused = fuse_prompt(state["template_description"], user_prompt)
        return fused
    except Exception as e:
        return f"融合失败: {str(e)}"


def generate_single(fused_prompt, product_image, aspect_ratio):
    """单图生成"""
    if not fused_prompt:
        return [], "请先融合 prompt"
    
    try:
        result_paths = generate_image(
            prompt=fused_prompt,
            style_references=state.get("representative_paths", []),
            product_reference=product_image,
            aspect_ratio=aspect_ratio,
        )
        return result_paths, f"✅ 生成成功: {len(result_paths)} 张"
    except Exception as e:
        return [], f"❌ 生成失败: {str(e)}"


def generate_batch(product_image, aspect_ratio, scene1, scene2, scene3, scene4, scene5):
    """批量生成"""
    if not state["template_description"]:
        return [], "请先分析风格"
    
    selected = []
    if scene1: selected.append(0)
    if scene2: selected.append(1)
    if scene3: selected.append(2)
    if scene4: selected.append(3)
    if scene5: selected.append(4)
    
    if not selected:
        return [], "请至少选择一个场景"
    
    generated = []
    logs = []
    
    for idx in selected:
        name, prompt = SCENES[idx]
        logs.append(f"🎨 生成: {name}")
        
        try:
            fused = fuse_prompt(state["template_description"], prompt)
            result_paths = generate_image(
                prompt=fused,
                style_references=state.get("representative_paths", []),
                product_reference=product_image,
                aspect_ratio=aspect_ratio,
            )
            
            for path in result_paths:
                new_name = f"batch_{idx}_{name}.png"
                new_path = os.path.join(os.path.dirname(path), new_name)
                shutil.move(path, new_path)
                generated.append(new_path)
                logs.append(f"   ✅ {name}")
                
        except Exception as e:
            logs.append(f"   ❌ {name}: {str(e)}")
    
    return generated, "\n".join(logs)


# 创建界面
with gr.Blocks(title="风格模板工具 V2") as demo:
    gr.Markdown("# 🎨 风格模板自动化工具 V2")
    gr.Markdown("## 双参考图模式：风格参考 + 产品参考 | 批量生成电商套图")
    
    with gr.Tab("📸 步骤1: 分析风格"):
        with gr.Row():
            upload_images = gr.File(label="上传风格图集", file_count="multiple", file_types=["image"])
            analyze_btn = gr.Button("🔍 分析风格")
        
        style_desc = gr.Textbox(label="风格描述", lines=8)
        rep_gallery = gr.Gallery(label="代表图")
    
    with gr.Tab("🔄 步骤2: 融合Prompt"):
        user_input = gr.Textbox(label="用户Prompt", lines=3, placeholder="描述要生成的内容...")
        fuse_btn = gr.Button("🔗 融合")
        fused_output = gr.Textbox(label="融合后的Prompt", lines=5)
    
    with gr.Tab("🎨 步骤3: 单图生成"):
        with gr.Row():
            with gr.Column():
                fused_prompt = gr.Textbox(label="融合Prompt", lines=3)
                product_img = gr.Image(label="产品参考图", type="filepath")
                aspect = gr.Dropdown(label="宽高比", choices=["1:1", "3:4", "4:3", "16:9"], value="3:4")
                gen_btn = gr.Button("🚀 生成")
            with gr.Column():
                result_gallery = gr.Gallery(label="生成结果")
                gen_log = gr.Textbox(label="日志")
    
    with gr.Tab("📦 步骤4: 批量生成套图"):
        with gr.Row():
            with gr.Column():
                batch_product = gr.Image(label="产品参考图", type="filepath")
                batch_aspect = gr.Dropdown(label="宽高比", choices=["1:1", "3:4", "4:3", "16:9"], value="3:4")
                
                gr.Markdown("**选择场景:**")
                c1 = gr.Checkbox(label="🎯 产品主图")
                c2 = gr.Checkbox(label="✨ 功效展示图")
                c3 = gr.Checkbox(label="🔬 成分说明图")
                c4 = gr.Checkbox(label="🛁 使用场景图")
                c5 = gr.Checkbox(label="📖 品牌故事图")
                
                batch_btn = gr.Button("📦 批量生成")
            
            with gr.Column():
                batch_gallery = gr.Gallery(label="批量生成结果")
                batch_log = gr.Textbox(label="生成日志", lines=10)
    
    # 事件绑定
    analyze_btn.click(analyze_style, inputs=upload_images, outputs=[style_desc, rep_gallery])
    fuse_btn.click(fuse, inputs=user_input, outputs=fused_output)
    gen_btn.click(generate_single, inputs=[fused_prompt, product_img, aspect], outputs=[result_gallery, gen_log])
    batch_btn.click(generate_batch, inputs=[batch_product, batch_aspect, c1, c2, c3, c4, c5], outputs=[batch_gallery, batch_log])


if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860, share=True)
