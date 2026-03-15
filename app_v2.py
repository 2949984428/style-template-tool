"""
风格模板自动化工具 V2 — Gradio Web UI
新增：批量生成套图、双参考图模式、电商场景预设
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

# ─── 全局状态 ───
state = {
    "template_description": "",
    "representative_paths": [],  # 风格参考图（来自模板）
    "all_image_paths": [],
    "product_reference": None,   # 产品参考图（用户上传）
}

# ─── 电商场景预设 ───
ECOMMERCE_SCENES = [
    {
        "name": "产品主图",
        "prompt": "product photography on clean white background, professional e-commerce style, minimalist aesthetic, soft diffused lighting, centered composition, sharp focus on product details",
        "icon": "🎯"
    },
    {
        "name": "功效展示图", 
        "prompt": "showcasing efficacy and benefits, with data visualization, clean infographic style, minimalist design, professional product photography, highlighting key results",
        "icon": "✨"
    },
    {
        "name": "成分说明图",
        "prompt": "highlighting ingredients, scientific formula visualization, clean laboratory aesthetic, minimalist design, professional product photography, ingredient highlights",
        "icon": "🔬"
    },
    {
        "name": "使用场景图",
        "prompt": "in lifestyle setting, bathroom vanity scene, clean and minimal aesthetic, soft natural lighting, professional product photography, elegant composition",
        "icon": "🛁"
    },
    {
        "name": "品牌故事图",
        "prompt": "brand story visualization, laboratory background, scientific professionalism, clean minimalist design, soft lighting, premium brand identity",
        "icon": "📖"
    },
    {
        "name": "对比展示图",
        "prompt": "before and after comparison, split screen showing results, clean infographic style, professional product photography, data visualization",
        "icon": "⚖️"
    },
]


# ─── 阶段1：图集分析 ───

def run_analysis(images):
    """上传图集 → 分析风格 → 输出描述 + 代表图"""
    if not images:
        return "请先上传图片", [], "", []

    image_paths = [img if isinstance(img, str) else img.name for img in images]
    state["all_image_paths"] = image_paths

    try:
        description, rep_indices, rep_paths = analyze_images(image_paths)
    except Exception as e:
        return f"分析失败：{str(e)}", [], "", []

    state["template_description"] = description
    state["representative_paths"] = rep_paths

    # 准备预览图
    rep_previews = []
    for path in rep_paths:
        if os.path.exists(path):
            rep_previews.append(path)

    return description, rep_previews, f"已选择 {len(rep_paths)} 张代表图", rep_paths


# ─── 阶段2：融合 Prompt ───

def run_fusion(template_desc, user_prompt):
    """融合模板描述 + 用户 prompt"""
    if not template_desc.strip():
        return "模板描述为空，请先在第一步生成"
    if not user_prompt.strip():
        return "请输入用户 prompt"

    try:
        fused = fuse_prompt(template_desc, user_prompt)
    except Exception as e:
        return f"融合失败：{str(e)}"

    return fused


# ─── 阶段3：单图生成 ───

def run_generate(fused_prompt, product_image, aspect_ratio, use_style_ref=True, use_product_ref=True):
    """生成单张图片"""
    if not fused_prompt.strip():
        return [], "请先融合 prompt"

    # 准备参考图
    style_refs = state.get("representative_paths", []) if use_style_ref else []
    product_ref = None
    
    if use_product_ref and product_image:
        if isinstance(product_image, str):
            product_ref = product_image
        else:
            product_ref = product_image.name
        state["product_reference"] = product_ref

    try:
        result_paths = generate_image(
            prompt=fused_prompt,
            style_references=style_refs if style_refs else None,
            product_reference=product_ref,
            aspect_ratio=aspect_ratio,
        )
    except Exception as e:
        return [], f"生成失败：{str(e)}"

    return result_paths, f"✅ 成功生成 {len(result_paths)} 张图片"


# ─── 阶段4：批量生成套图 ───

def run_batch_generate(template_desc, product_image, aspect_ratio, selected_scenes, custom_prompts):
    """批量生成电商套图"""
    if not template_desc.strip():
        return [], "请先完成第一步：分析风格图集"
    
    if not selected_scenes:
        return [], "请至少选择一个场景"

    # 准备参考图
    style_refs = state.get("representative_paths", [])
    product_ref = None
    
    if product_image:
        if isinstance(product_image, str):
            product_ref = product_image
        else:
            product_ref = product_image.name

    generated_files = []
    logs = []
    
    # 解析选择的场景
    scene_indices = [int(x) for x in selected_scenes if x.isdigit()]
    
    for idx in scene_indices:
        if idx < 0 or idx >= len(ECOMMERCE_SCENES):
            continue
            
        scene = ECOMMERCE_SCENES[idx]
        scene_name = scene["name"]
        
        # 使用自定义 prompt 或默认 prompt
        if custom_prompts and idx < len(custom_prompts) and custom_prompts[idx].strip():
            scene_prompt = custom_prompts[idx]
        else:
            scene_prompt = scene["prompt"]
        
        logs.append(f"🎨 生成场景: {scene_name}")
        
        try:
            # 融合 prompt
            fused = fuse_prompt(template_desc, scene_prompt)
            
            # 生成图片
            result_paths = generate_image(
                prompt=fused,
                style_references=style_refs if style_refs else None,
                product_reference=product_ref,
                aspect_ratio=aspect_ratio,
            )
            
            # 重命名文件
            for path in result_paths:
                timestamp = datetime.now().strftime("%m%d_%H%M%S")
                new_name = f"batch_{timestamp}_{idx:02d}_{scene_name.replace(' ', '_')}.png"
                new_path = os.path.join(os.path.dirname(path), new_name)
                shutil.move(path, new_path)
                generated_files.append(new_path)
                logs.append(f"   ✅ {scene_name}: {new_name}")
                
        except Exception as e:
            logs.append(f"   ❌ {scene_name}: {str(e)}")

    return generated_files, "\n".join(logs)


# ─── 辅助功能 ───

def get_scene_info():
    """获取场景信息用于显示"""
    info = []
    for i, scene in enumerate(ECOMMERCE_SCENES):
        info.append(f"{scene['icon']} {i}. {scene['name']}")
    return "\n".join(info)


def on_scene_select(selected):
    """场景选择回调"""
    if not selected:
        return ""
    
    prompts = []
    for idx in selected:
        scene = ECOMMERCE_SCENES[idx]
        prompts.append(f"【{scene['name']}】\n{scene['prompt']}\n")
    
    return "\n".join(prompts)


# ─── Gradio UI ───

def create_ui():
    """创建 Gradio UI"""
    
    with gr.Blocks(
        title="风格模板自动化工具 V2",
        theme=gr.themes.Soft(),
        css="""
        .container { max-width: 1400px; margin: 0 auto; }
        .stage-title { font-size: 1.5em; font-weight: bold; margin-bottom: 10px; color: #333; }
        .stage-box { border: 2px solid #e0e0e0; border-radius: 10px; padding: 20px; margin-bottom: 20px; }
        .output-box { background: #f5f5f5; border-radius: 8px; padding: 15px; }
        .hint-text { color: #666; font-size: 0.9em; }
        .batch-item { border: 1px solid #ddd; border-radius: 5px; padding: 10px; margin: 5px 0; }
        """
    ) as demo:
        
        gr.Markdown("# 🎨 风格模板自动化工具 V2")
        gr.Markdown("### 双参考图模式：风格参考 + 产品参考 | 批量生成电商套图")
        
        # ─── 阶段1：风格分析 ───
        with gr.Column(variant="panel"):
            gr.Markdown("### 📸 阶段1：上传风格图集并分析", elem_classes="stage-title")
            
            with gr.Row():
                with gr.Column(scale=2):
                    upload_images = gr.File(
                        label="上传风格图集（建议5-10张）",
                        file_count="multiple",
                        file_types=["image"],
                    )
                    analyze_btn = gr.Button("🔍 分析风格", variant="primary")
                    
                with gr.Column(scale=3):
                    style_description = gr.Textbox(
                        label="📝 风格模板描述（可编辑）",
                        lines=10,
                        placeholder="点击'分析风格'后，这里会显示分析结果...",
                    )
                    
            with gr.Row():
                rep_gallery = gr.Gallery(
                    label="🖼️ 自动选择的代表图",
                    columns=3,
                    rows=1,
                    height=200,
                )
                rep_info = gr.Textbox(label="代表图信息", interactive=False)
        
        # ─── 阶段2：Prompt 融合 ───
        with gr.Column(variant="panel"):
            gr.Markdown("### 🔄 阶段2：融合用户 Prompt", elem_classes="stage-title")
            
            with gr.Row():
                with gr.Column(scale=1):
                    user_prompt = gr.Textbox(
                        label="💡 用户 Prompt",
                        lines=3,
                        placeholder="描述你想要生成的内容，例如：CeraVe SA洁面产品...",
                    )
                    fusion_btn = gr.Button("🔗 融合 Prompt", variant="primary")
                    
                with gr.Column(scale=2):
                    fused_result = gr.Textbox(
                        label="✨ 融合后的 Prompt（可直接使用或修改）",
                        lines=5,
                        placeholder="融合后的结果会显示在这里...",
                    )
        
        # ─── 阶段3：单图生成 ───
        with gr.Column(variant="panel"):
            gr.Markdown("### 🎨 阶段3：单图生成", elem_classes="stage-title")
            
            with gr.Row():
                with gr.Column(scale=1):
                    product_image = gr.Image(
                        label="📦 产品参考图（可选）",
                        type="filepath",
                    )
                    
                    with gr.Row():
                        use_style = gr.Checkbox(label="使用风格参考图", value=True)
                        use_product = gr.Checkbox(label="使用产品参考图", value=True)
                    
                    aspect_ratio = gr.Dropdown(
                        label="📐 宽高比",
                        choices=["1:1", "3:4", "4:3", "16:9"],
                        value="3:4",
                    )
                    
                    generate_btn = gr.Button("🚀 生成图片", variant="primary")
                    
                with gr.Column(scale=2):
                    output_gallery = gr.Gallery(
                        label="🖼️ 生成结果",
                        columns=2,
                        rows=2,
                        height=400,
                    )
                    generate_log = gr.Textbox(label="生成日志", interactive=False)
        
        # ─── 阶段4：批量生成套图 ───
        with gr.Column(variant="panel"):
            gr.Markdown("### 📦 阶段4：批量生成电商套图", elem_classes="stage-title")
            
            with gr.Row():
                with gr.Column(scale=1):
                    gr.Markdown("**选择要生成的场景：**")
                    scene_checkboxes = []
                    for i, scene in enumerate(ECOMMERCE_SCENES):
                        cb = gr.Checkbox(label=f"{scene['icon']} {scene['name']}", value=False)
                        scene_checkboxes.append(cb)
                    
                    batch_product = gr.Image(
                        label="📦 产品参考图（批量生成）",
                        type="filepath",
                    )
                    
                    batch_aspect = gr.Dropdown(
                        label="📐 宽高比",
                        choices=["1:1", "3:4", "4:3", "16:9"],
                        value="3:4",
                    )
                    
                    batch_btn = gr.Button("📦 批量生成套图", variant="primary")
                    
                with gr.Column(scale=2):
                    batch_gallery = gr.Gallery(
                        label="🖼️ 批量生成结果",
                        columns=3,
                        rows=2,
                        height=500,
                    )
                    batch_log = gr.Textbox(
                        label="批量生成日志",
                        lines=10,
                        interactive=False,
                    )
        
        # ─── 事件绑定 ───
        
        # 阶段1：分析风格
        analyze_btn.click(
            fn=run_analysis,
            inputs=[upload_images],
            outputs=[style_description, rep_gallery, rep_info, gr.State()],
        )
        
        # 阶段2：融合 Prompt
        fusion_btn.click(
            fn=run_fusion,
            inputs=[style_description, user_prompt],
            outputs=[fused_result],
        )
        
        # 阶段3：单图生成
        generate_btn.click(
            fn=run_generate,
            inputs=[fused_result, product_image, aspect_ratio, use_style, use_product],
            outputs=[output_gallery, generate_log],
        )
        
        # 阶段4：批量生成
        def get_selected_scenes(*checkboxes):
            return [i for i, cb in enumerate(checkboxes) if cb]
        
        batch_btn.click(
            fn=lambda *args: run_batch_generate(
                args[0],  # template_desc
                args[1],  # product_image
                args[2],  # aspect_ratio
                [i for i, cb in enumerate(args[3:3+len(ECOMMERCE_SCENES)]) if cb],
                [],  # custom_prompts (简化版)
            ),
            inputs=[style_description, batch_product, batch_aspect] + scene_checkboxes,
            outputs=[batch_gallery, batch_log],
        )
        
        gr.Markdown("---")
        gr.Markdown("💡 **使用提示**：\n1. 上传风格图集（如The Ordinary电商图）→ 2. 分析风格 → 3. 输入产品信息 → 4. 选择单图或批量生成")
    
    return demo


if __name__ == "__main__":
    demo = create_ui()
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        show_error=True,
    )
