"""
风格模板自动化工具 — Gradio Web UI
覆盖完整 3 阶段：模板描述生成 → 融合 Prompt → 生成图片
UI：现代暗色液态玻璃风格 (shadcn-inspired)
"""

import os
import sys
import gradio as gr

# 确保项目根目录在 path 中
sys.path.insert(0, os.path.dirname(__file__))

import config
from core.analyzer import analyze_images
from core.fusion import fuse_prompt
from core.generator import generate_image

# ─── 全局状态 ───
state = {
    "template_description": "",
    "representative_paths": [],
    "all_image_paths": [],
}


# ─── 阶段1：图集分析 ───

def run_analysis(images):
    """上传图集 → 分析风格 → 输出描述 + 代表图"""
    if not images:
        return "请先上传图片", [], ""

    image_paths = [img if isinstance(img, str) else img.name for img in images]
    state["all_image_paths"] = image_paths

    try:
        description, rep_indices = analyze_images(image_paths)
    except Exception as e:
        return f"分析失败：{str(e)}", [], ""

    state["template_description"] = description

    rep_paths = []
    for idx in rep_indices:
        if 1 <= idx <= len(image_paths):
            rep_paths.append(image_paths[idx - 1])
    if not rep_paths:
        rep_paths = [image_paths[0]]
    state["representative_paths"] = rep_paths

    return description, rep_paths, description


# ─── 阶段2：融合 Prompt ───

def run_fusion(template_desc, user_prompt):
    """融合模板描述 + 用户 prompt"""
    if not template_desc.strip():
        return "模板描述为空，请先在第一步生成"
    if not user_prompt.strip():
        return "请输入用户 prompt"

    state["template_description"] = template_desc

    try:
        fused = fuse_prompt(template_desc, user_prompt)
    except Exception as e:
        return f"融合失败：{str(e)}"

    return fused


# ─── 阶段3：生成图片 ───

def run_generate(fused_prompt, user_ref_images, aspect_ratio):
    """生成图片"""
    if not fused_prompt.strip():
        return [], "请先融合 prompt"

    ref_paths = list(state.get("representative_paths", []))
    if user_ref_images:
        for img in user_ref_images:
            path = img if isinstance(img, str) else img.name
            ref_paths.append(path)

    try:
        result_paths = generate_image(
            prompt=fused_prompt,
            reference_images=ref_paths if ref_paths else None,
            aspect_ratio=aspect_ratio,
        )
    except Exception as e:
        return [], f"生成失败：{str(e)}"

    return result_paths, f"成功生成 {len(result_paths)} 张图片"


# ─── 批量测试 ───

def run_batch(template_desc, prompt1, prompt2, prompt3, aspect_ratio):
    """批量测试 3 组"""
    results = [[], [], []]
    messages = []
    state["template_description"] = template_desc
    ref_paths = state.get("representative_paths", [])

    for i, user_prompt in enumerate([prompt1, prompt2, prompt3]):
        if not user_prompt.strip():
            messages.append(f"案例 {i+1}：已跳过（prompt 为空）")
            continue
        try:
            fused = fuse_prompt(template_desc, user_prompt)
            paths = generate_image(
                prompt=fused,
                reference_images=ref_paths if ref_paths else None,
                aspect_ratio=aspect_ratio,
            )
            results[i] = paths
            messages.append(f"案例 {i+1}：生成 {len(paths)} 张")
        except Exception as e:
            messages.append(f"案例 {i+1}：失败 - {str(e)}")

    return results[0], results[1], results[2], "\n".join(messages)


# ─── 液态玻璃暗色 CSS ───

CUSTOM_CSS = """
/* ── 全局基础 ── */
:root {
    --glass-bg: rgba(16, 16, 20, 0.6);
    --glass-border: rgba(255, 255, 255, 0.06);
    --glass-hover: rgba(255, 255, 255, 0.08);
    --glass-blur: 24px;
    --accent: #a78bfa;
    --accent-glow: rgba(167, 139, 250, 0.15);
    --accent-hover: #c4b5fd;
    --text-primary: #f4f4f5;
    --text-secondary: #a1a1aa;
    --text-muted: #52525b;
    --surface: rgba(24, 24, 27, 0.8);
    --radius: 16px;
    --radius-sm: 10px;
    --transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}

body, .gradio-container {
    background: #09090b !important;
    color: var(--text-primary) !important;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Inter', sans-serif !important;
}

.gradio-container {
    max-width: 1280px !important;
    margin: 0 auto !important;
}

/* ── 大背景装饰 ── */
.gradio-container::before {
    content: '';
    position: fixed;
    top: -40%;
    left: -20%;
    width: 80%;
    height: 80%;
    background: radial-gradient(ellipse, rgba(139, 92, 246, 0.08) 0%, transparent 60%);
    pointer-events: none;
    z-index: 0;
}
.gradio-container::after {
    content: '';
    position: fixed;
    bottom: -30%;
    right: -10%;
    width: 60%;
    height: 60%;
    background: radial-gradient(ellipse, rgba(59, 130, 246, 0.05) 0%, transparent 60%);
    pointer-events: none;
    z-index: 0;
}

/* ── Header 标题 ── */
.markdown-text h1 {
    font-size: 2rem !important;
    font-weight: 700 !important;
    letter-spacing: -0.03em !important;
    background: linear-gradient(135deg, #f4f4f5 0%, #a78bfa 50%, #818cf8 100%) !important;
    -webkit-background-clip: text !important;
    -webkit-text-fill-color: transparent !important;
    background-clip: text !important;
    padding-bottom: 4px !important;
}
.markdown-text p, .markdown-text h3 {
    color: var(--text-secondary) !important;
}
.markdown-text h3 {
    font-size: 0.95rem !important;
    font-weight: 500 !important;
    letter-spacing: -0.01em !important;
    color: var(--text-muted) !important;
    border: none !important;
}

/* ── Tab 导航 ── */
.tab-nav {
    background: var(--glass-bg) !important;
    backdrop-filter: blur(var(--glass-blur)) !important;
    -webkit-backdrop-filter: blur(var(--glass-blur)) !important;
    border: 1px solid var(--glass-border) !important;
    border-radius: 14px !important;
    padding: 6px !important;
    margin-bottom: 20px !important;
    gap: 4px !important;
}
.tab-nav button {
    font-size: 14px !important;
    font-weight: 500 !important;
    color: var(--text-secondary) !important;
    background: transparent !important;
    border: none !important;
    border-radius: 10px !important;
    padding: 10px 20px !important;
    transition: var(--transition) !important;
}
.tab-nav button:hover {
    background: var(--glass-hover) !important;
    color: var(--text-primary) !important;
}
.tab-nav button.selected {
    background: rgba(167, 139, 250, 0.12) !important;
    color: var(--accent) !important;
    box-shadow: 0 0 20px rgba(167, 139, 250, 0.08) !important;
}

/* ── 面板/卡片容器 ── */
.block, .form, .panel {
    background: var(--glass-bg) !important;
    backdrop-filter: blur(var(--glass-blur)) !important;
    -webkit-backdrop-filter: blur(var(--glass-blur)) !important;
    border: 1px solid var(--glass-border) !important;
    border-radius: var(--radius) !important;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3), inset 0 1px 0 rgba(255, 255, 255, 0.04) !important;
    transition: var(--transition) !important;
}
.block:hover {
    border-color: rgba(255, 255, 255, 0.1) !important;
}

/* ── 输入框 ── */
textarea, input[type="text"], .wrap input {
    background: rgba(255, 255, 255, 0.03) !important;
    border: 1px solid rgba(255, 255, 255, 0.08) !important;
    border-radius: var(--radius-sm) !important;
    color: var(--text-primary) !important;
    font-family: 'SF Mono', 'JetBrains Mono', 'Fira Code', monospace !important;
    font-size: 13px !important;
    transition: var(--transition) !important;
    caret-color: var(--accent) !important;
}
textarea:focus, input[type="text"]:focus {
    border-color: rgba(167, 139, 250, 0.4) !important;
    box-shadow: 0 0 0 3px rgba(167, 139, 250, 0.1), 0 0 20px rgba(167, 139, 250, 0.05) !important;
    outline: none !important;
}
textarea::placeholder, input::placeholder {
    color: var(--text-muted) !important;
}

/* ── Label ── */
label, .label-wrap span {
    color: var(--text-secondary) !important;
    font-weight: 500 !important;
    font-size: 13px !important;
    letter-spacing: 0.01em !important;
}

/* ── 按钮 ── */
button.primary {
    background: linear-gradient(135deg, rgba(139, 92, 246, 0.8), rgba(99, 102, 241, 0.8)) !important;
    border: 1px solid rgba(167, 139, 250, 0.3) !important;
    border-radius: var(--radius-sm) !important;
    color: white !important;
    font-weight: 600 !important;
    font-size: 14px !important;
    letter-spacing: 0.01em !important;
    box-shadow: 0 4px 20px rgba(139, 92, 246, 0.25), inset 0 1px 0 rgba(255, 255, 255, 0.1) !important;
    transition: var(--transition) !important;
    backdrop-filter: blur(8px) !important;
}
button.primary:hover {
    background: linear-gradient(135deg, rgba(139, 92, 246, 0.95), rgba(99, 102, 241, 0.95)) !important;
    box-shadow: 0 8px 30px rgba(139, 92, 246, 0.35), inset 0 1px 0 rgba(255, 255, 255, 0.15) !important;
    transform: translateY(-1px) !important;
}
button.primary:active {
    transform: translateY(0) !important;
}

button.secondary {
    background: rgba(255, 255, 255, 0.04) !important;
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
    border-radius: var(--radius-sm) !important;
    color: var(--text-primary) !important;
    font-weight: 500 !important;
    backdrop-filter: blur(8px) !important;
    transition: var(--transition) !important;
}
button.secondary:hover {
    background: rgba(255, 255, 255, 0.08) !important;
    border-color: rgba(255, 255, 255, 0.18) !important;
}

button.lg {
    padding: 14px 28px !important;
    font-size: 15px !important;
    border-radius: 12px !important;
}

/* ── Dropdown ── */
.wrap .secondary-wrap, .wrap .dropdown {
    background: rgba(255, 255, 255, 0.03) !important;
    border: 1px solid rgba(255, 255, 255, 0.08) !important;
    border-radius: var(--radius-sm) !important;
    color: var(--text-primary) !important;
}
.wrap ul[role="listbox"] {
    background: rgba(24, 24, 27, 0.95) !important;
    backdrop-filter: blur(20px) !important;
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
    border-radius: var(--radius-sm) !important;
    box-shadow: 0 16px 48px rgba(0, 0, 0, 0.5) !important;
}
.wrap ul[role="listbox"] li {
    color: var(--text-primary) !important;
    transition: var(--transition) !important;
}
.wrap ul[role="listbox"] li:hover, .wrap ul[role="listbox"] li.selected {
    background: rgba(167, 139, 250, 0.12) !important;
    color: var(--accent) !important;
}

/* ── Gallery ── */
.gallery-item {
    background: var(--glass-bg) !important;
    border: 1px solid var(--glass-border) !important;
    border-radius: var(--radius-sm) !important;
    overflow: hidden !important;
    transition: var(--transition) !important;
}
.gallery-item:hover {
    border-color: rgba(167, 139, 250, 0.3) !important;
    box-shadow: 0 4px 20px rgba(167, 139, 250, 0.1) !important;
    transform: scale(1.02) !important;
}
.gallery-item img {
    border-radius: var(--radius-sm) !important;
}

/* ── 文件上传区 ── */
.upload-container, .file-preview {
    background: rgba(255, 255, 255, 0.02) !important;
    border: 2px dashed rgba(255, 255, 255, 0.08) !important;
    border-radius: var(--radius) !important;
    transition: var(--transition) !important;
}
.upload-container:hover, .file-preview:hover {
    border-color: rgba(167, 139, 250, 0.3) !important;
    background: rgba(167, 139, 250, 0.03) !important;
}

/* ── 滚动条 ── */
::-webkit-scrollbar {
    width: 6px;
    height: 6px;
}
::-webkit-scrollbar-track {
    background: transparent;
}
::-webkit-scrollbar-thumb {
    background: rgba(255, 255, 255, 0.1);
    border-radius: 3px;
}
::-webkit-scrollbar-thumb:hover {
    background: rgba(255, 255, 255, 0.2);
}

/* ── Row / Column 间距优化 ── */
.gap {
    gap: 16px !important;
}
.contain > .block {
    margin-bottom: 12px !important;
}

/* ── 状态信息 ── */
.status-success {
    color: #86efac !important;
}
.status-error {
    color: #fca5a5 !important;
}

/* ── 隐藏 Gradio 默认 footer ── */
footer {
    display: none !important;
}
"""


# ─── Gradio UI ───

def build_ui():
    with gr.Blocks(
        title="Style Template Tool",
        theme=gr.themes.Base(
            primary_hue=gr.themes.colors.violet,
            secondary_hue=gr.themes.colors.zinc,
            neutral_hue=gr.themes.colors.zinc,
            font=gr.themes.GoogleFont("Inter"),
            font_mono=gr.themes.GoogleFont("JetBrains Mono"),
        ),
        css=CUSTOM_CSS,
    ) as app:
        gr.Markdown("# Style Template Tool\n图集分析 → Prompt 融合 → 图片生成")

        # ─── Tab 1：模板描述生成 ───
        with gr.Tab("模板描述生成", id="tab-analyze"):
            gr.Markdown("### 上传风格图集，AI 自动提取风格特征")

            with gr.Row():
                with gr.Column(scale=1):
                    upload_gallery = gr.File(
                        label="上传风格图集（1-30 张）",
                        file_count="multiple",
                        file_types=["image"],
                    )
                    analyze_btn = gr.Button(
                        "生成模板描述",
                        variant="primary",
                        size="lg",
                    )

                with gr.Column(scale=1):
                    desc_output = gr.Textbox(
                        label="模板描述（可编辑）",
                        lines=20,
                        interactive=True,
                        placeholder="上传图集后点击按钮，AI 将分析风格特征...",
                    )

            rep_gallery = gr.Gallery(
                label="代表图",
                columns=3,
                height=250,
            )

            desc_for_tab2 = gr.Textbox(visible=False)

            analyze_btn.click(
                fn=run_analysis,
                inputs=[upload_gallery],
                outputs=[desc_output, rep_gallery, desc_for_tab2],
            )

        # ─── Tab 2：融合 & 生成 ───
        with gr.Tab("融合 & 生成", id="tab-fuse"):
            gr.Markdown("### 输入你的创意，与模板风格融合后生成图片")

            with gr.Row():
                with gr.Column(scale=1):
                    tab2_desc = gr.Textbox(
                        label="模板描述",
                        lines=10,
                        interactive=True,
                        placeholder="从第一步自动带入，也可手动编辑...",
                    )
                    user_prompt = gr.Textbox(
                        label="用户 Prompt",
                        lines=3,
                        placeholder="描述你想生成的画面内容...",
                    )
                    fuse_btn = gr.Button("融合 Prompt", variant="secondary")
                    fused_output = gr.Textbox(
                        label="融合后的 Prompt（可微调）",
                        lines=8,
                        interactive=True,
                    )

                with gr.Column(scale=1):
                    user_ref_upload = gr.File(
                        label="用户参考图（可选）",
                        file_count="multiple",
                        file_types=["image"],
                    )
                    aspect_select = gr.Dropdown(
                        label="宽高比",
                        choices=["1:1", "16:9", "4:3", "3:2", "9:16", "3:4"],
                        value="1:1",
                    )
                    gen_btn = gr.Button("生成图片", variant="primary", size="lg")
                    gen_status = gr.Textbox(label="状态", interactive=False)

            gen_gallery = gr.Gallery(label="生成结果", columns=3, height=400)

            desc_output.change(fn=lambda x: x, inputs=[desc_output], outputs=[tab2_desc])

            fuse_btn.click(
                fn=run_fusion,
                inputs=[tab2_desc, user_prompt],
                outputs=[fused_output],
            )

            gen_btn.click(
                fn=run_generate,
                inputs=[fused_output, user_ref_upload, aspect_select],
                outputs=[gen_gallery, gen_status],
            )

        # ─── Tab 3：批量测试 ───
        with gr.Tab("批量测试", id="tab-batch"):
            gr.Markdown("### 三组测试案例，快速验证风格一致性")

            tab3_desc = gr.Textbox(
                label="模板描述",
                lines=6,
                interactive=True,
            )
            desc_output.change(fn=lambda x: x, inputs=[desc_output], outputs=[tab3_desc])

            batch_aspect = gr.Dropdown(
                label="宽高比",
                choices=["1:1", "16:9", "4:3", "3:2"],
                value="1:1",
            )

            with gr.Row():
                p1 = gr.Textbox(
                    label="案例 1",
                    lines=2,
                    value="A serene mountain landscape at sunrise",
                )
                p2 = gr.Textbox(
                    label="案例 2",
                    lines=2,
                    value="A cozy coffee shop interior with warm lighting",
                )
                p3 = gr.Textbox(
                    label="案例 3",
                    lines=2,
                    value="A portrait of a young woman in a garden",
                )

            batch_btn = gr.Button("批量生成", variant="primary", size="lg")
            batch_status = gr.Textbox(label="状态", interactive=False)

            with gr.Row():
                g1 = gr.Gallery(label="案例 1", columns=2, height=300)
                g2 = gr.Gallery(label="案例 2", columns=2, height=300)
                g3 = gr.Gallery(label="案例 3", columns=2, height=300)

            batch_btn.click(
                fn=run_batch,
                inputs=[tab3_desc, p1, p2, p3, batch_aspect],
                outputs=[g1, g2, g3, batch_status],
            )

    return app


if __name__ == "__main__":
    if not config.GEMINI_API_KEY:
        print("\n  请先设置环境变量 GEMINI_API_KEY")
        print("  export GEMINI_API_KEY='你的API Key'\n")
        sys.exit(1)

    app = build_ui()
    app.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
    )
