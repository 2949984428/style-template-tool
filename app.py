"""
风格模板自动化工具 — Gradio Web UI
三阶段：图集分析 → Prompt 融合 → 图片生成
支持智能双参考图 / 单参考图自动选择
"""

import os
import sys

import gradio as gr

sys.path.insert(0, os.path.dirname(__file__))

import config
from core.analyzer import analyze_images
from core.fusion import fuse_prompt
from core.generator import generate_image
from core.utils import setup_logging, get_logger
from generate_smart_set import _get_style_only_prompt

setup_logging()
logger = get_logger("app")

# ── 全局状态 ──

_state: dict = {
    "description": "",
    "rep_paths": [],
    "all_paths": [],
    "analysis_list": [],
}


def _to_paths(files) -> list:
    if not files:
        return []
    return [f if isinstance(f, str) else f.name for f in files]


def _single_path(f):
    if f is None:
        return None
    return f if isinstance(f, str) else getattr(f, "name", str(f))


# ─── 阶段 1：分析 ───


def run_analysis(images, detailed):
    if not images:
        return "请先上传图片", [], "", ""

    paths = _to_paths(images)
    _state["all_paths"] = paths

    try:
        if detailed:
            desc, rep_idx, _, a_list = analyze_images(paths, detailed=True)
            _state["analysis_list"] = a_list

            lines = []
            for item in a_list:
                idx = item["image_index"]
                cat = item.get("design_category", "?")
                has = item.get("has_subject", "?")
                typ = item.get("image_type", "?")
                subj = item.get("subject_description", "")
                rep = " ⭐" if item.get("is_representative") else ""
                mode = "双参考图" if has else "单参考图"
                lines.append(
                    f"#{idx}{rep}  [{cat}] {typ}  "
                    f"主体={'有' if has else '无'} → {mode}"
                )
                if subj:
                    lines.append(f"   └ {subj}")
            analysis_md = "\n".join(lines)
        else:
            desc, rep_idx, _ = analyze_images(paths)
            _state["analysis_list"] = []
            analysis_md = ""
    except Exception as e:
        logger.exception("分析失败")
        return f"分析失败：{e}", [], "", ""

    _state["description"] = desc

    rep_display = [paths[i - 1] for i in rep_idx if 1 <= i <= len(paths)]
    if not rep_display and paths:
        rep_display = [paths[0]]
    _state["rep_paths"] = rep_display

    return desc, rep_display, desc, analysis_md


# ─── 阶段 2：融合 ───


def run_fusion(template_desc, user_prompt):
    if not template_desc.strip():
        return "模板描述为空，请先完成风格分析"
    if not user_prompt.strip():
        return "请输入用户 Prompt"

    _state["description"] = template_desc
    try:
        return fuse_prompt(template_desc, user_prompt)
    except Exception as e:
        logger.exception("融合失败")
        return f"融合失败：{e}"


# ─── 阶段 3：生成 ───


def run_generate(fused_prompt, product_img, aspect):
    if not fused_prompt.strip():
        return [], "请先融合 Prompt"

    style_refs = list(_state.get("rep_paths", []))
    prod = _single_path(product_img)
    tag = "双参考图" if prod else "风格参考图"

    try:
        paths = generate_image(
            prompt=fused_prompt,
            style_references=style_refs or None,
            product_reference=prod,
            aspect_ratio=aspect,
        )
    except Exception as e:
        logger.exception("生成失败")
        return [], f"生成失败：{e}"

    return paths, f"{tag} — 生成 {len(paths)} 张图片"


# ─── 智能套图（generator 流式输出） ───


def run_smart_set(ref_images, product_img, product_name, aspect):
    if not ref_images:
        yield [], "请上传参考图集", ""
        return

    ref_paths = _to_paths(ref_images)
    prod = _single_path(product_img)
    name = product_name.strip() or "Product"

    log_lines = ["正在分析图集…"]
    yield [], "\n".join(log_lines), ""

    try:
        desc, _, _, a_list = analyze_images(ref_paths, detailed=True)
    except Exception as e:
        logger.exception("分析失败")
        yield [], f"分析失败: {e}", ""
        return

    log_lines[0] = f"分析完成 — {len(ref_paths)} 张参考图"
    log_lines.append("")
    for item in a_list:
        idx = item["image_index"]
        has = item.get("has_subject", True)
        typ = item.get("image_type", "?")
        log_lines.append(f"  #{idx} [{typ}] → {'双参考图' if has else '单参考图'}")
    log_lines.append("")
    log_lines.append("开始逐张生成…")
    log_lines.append("")
    yield [], "\n".join(log_lines), desc

    style_desc = desc[:200] if desc else ""
    all_results = []

    for item in a_list:
        idx = item["image_index"]
        ref_path = item["image_path"]
        has_subject = item.get("has_subject", True)
        image_type = item.get("image_type", "product_hero")
        category = item.get("design_category", "ecommerce")

        if has_subject and prod:
            prompt_text = f"{name} professional {image_type} photography, {style_desc}"
            try:
                paths = generate_image(
                    prompt=prompt_text,
                    style_references=[ref_path],
                    product_reference=prod,
                    aspect_ratio=aspect,
                )
                all_results.extend(paths)
                log_lines.append(f"  ✓ #{idx} 双参考图 — {len(paths)} 张")
            except Exception as e:
                log_lines.append(f"  ✗ #{idx} 失败: {e}")
        else:
            prompt_text = _get_style_only_prompt(category, image_type, name, style_desc)
            try:
                paths = generate_image(
                    prompt=prompt_text,
                    style_references=[ref_path],
                    product_reference=None,
                    aspect_ratio=aspect,
                )
                all_results.extend(paths)
                log_lines.append(f"  ✓ #{idx} 单参考图 — {len(paths)} 张")
            except Exception as e:
                log_lines.append(f"  ✗ #{idx} 失败: {e}")

        yield all_results[:], "\n".join(log_lines), desc

    log_lines.append("")
    log_lines.append(f"全部完成! 共生成 {len(all_results)} 张")
    yield all_results, "\n".join(log_lines), desc


# ─── Theme + CSS ───

_COLORS = {
    "bg_root": "#0b0f19",
    "bg_card": "#111827",
    "bg_input": "#030712",
    "border_subtle": "#1f2937",
    "accent": "#8b5cf6",
}


def _midnight_theme():
    return gr.themes.Base(
        primary_hue=gr.themes.colors.violet,
        secondary_hue=gr.themes.colors.slate,
        neutral_hue=gr.themes.colors.gray,
        font=gr.themes.GoogleFont("Inter"),
        font_mono=gr.themes.GoogleFont("JetBrains Mono"),
    ).set(
        body_background_fill=_COLORS["bg_root"],
        body_background_fill_dark=_COLORS["bg_root"],
        block_background_fill=_COLORS["bg_card"],
        block_background_fill_dark=_COLORS["bg_card"],
        block_border_width="1px",
        block_border_color=_COLORS["border_subtle"],
        block_border_color_dark=_COLORS["border_subtle"],
        input_background_fill=_COLORS["bg_input"],
        input_background_fill_dark=_COLORS["bg_input"],
        button_primary_background_fill=_COLORS["accent"],
        button_primary_background_fill_dark=_COLORS["accent"],
        button_primary_border_color=_COLORS["accent"],
        button_primary_text_color="white",
    )


CUSTOM_CSS = """
body { background-color: #0b0f19 !important; color: #f9fafb !important; }
.gradio-container { max-width: 1400px !important; margin: 0 auto !important; padding: 32px !important; }

#header-block { text-align: center; margin-bottom: 40px !important; background: transparent !important; border: none !important; box-shadow: none !important; }
#header-block h1 { font-size: 3rem !important; font-weight: 800 !important; letter-spacing: -0.05em !important; margin-bottom: 12px !important; background: linear-gradient(to right, #c084fc, #6366f1) !important; -webkit-background-clip: text !important; -webkit-text-fill-color: transparent !important; }
#header-block p { font-size: 1.1rem !important; color: #9ca3af !important; }

.block, .panel { background-color: #111827 !important; border: 1px solid #1f2937 !important; border-radius: 12px !important; overflow: hidden !important; }

.tab-nav { border: none !important; background: transparent !important; gap: 24px !important; }
.tab-nav button { background: transparent !important; border: none !important; color: #6b7280 !important; font-weight: 600 !important; font-size: 1rem !important; padding: 12px 0 !important; border-bottom: 2px solid transparent !important; border-radius: 0 !important; }
.tab-nav button:hover { color: #d1d5db !important; }
.tab-nav button.selected { color: #c084fc !important; border-bottom-color: #c084fc !important; background: transparent !important; box-shadow: none !important; }

textarea, input[type="text"], .wrap .dropdown, .wrap .secondary-wrap { background-color: #030712 !important; border: 1px solid #1f2937 !important; border-radius: 8px !important; color: #f3f4f6 !important; font-size: 0.95rem !important; padding: 12px !important; }
textarea:focus, input[type="text"]:focus { border-color: #8b5cf6 !important; box-shadow: 0 0 0 2px rgba(139,92,246,0.2) !important; outline: none !important; }

label span, .label-wrap span { color: #9ca3af !important; font-size: 0.85rem !important; font-weight: 600 !important; text-transform: uppercase !important; letter-spacing: 0.05em !important; }

button.primary { background: linear-gradient(135deg, #8b5cf6, #6366f1) !important; border: none !important; color: white !important; font-weight: 600 !important; padding: 12px 24px !important; border-radius: 8px !important; box-shadow: 0 4px 6px rgba(139,92,246,0.3) !important; }
button.primary:hover { transform: translateY(-1px) !important; box-shadow: 0 6px 8px rgba(139,92,246,0.4) !important; }
button.secondary { background-color: #1f2937 !important; color: #e5e7eb !important; border: 1px solid #374151 !important; border-radius: 8px !important; }
button.secondary:hover { background-color: #374151 !important; }

.upload-container { background-color: #0f131d !important; border: 2px dashed #374151 !important; border-radius: 12px !important; min-height: 160px !important; }
.upload-container:hover { border-color: #8b5cf6 !important; background-color: rgba(139,92,246,0.05) !important; }

.gallery-item { border-radius: 8px !important; border: 1px solid #1f2937 !important; overflow: hidden !important; background-color: #030712 !important; }
.gallery-item.selected { border-color: #8b5cf6 !important; box-shadow: 0 0 0 2px #8b5cf6 !important; }

#smart-log textarea, #gen-status textarea { font-family: 'JetBrains Mono', monospace !important; font-size: 0.85rem !important; color: #a5f3fc !important; background-color: #0f172a !important; border: 1px solid #1e293b !important; }

footer { display: none !important; }
::-webkit-scrollbar { width: 8px; height: 8px; }
::-webkit-scrollbar-track { background: #111827; }
::-webkit-scrollbar-thumb { background: #374151; border-radius: 4px; }
"""


# ─── UI ───


def build_ui():
    with gr.Blocks(title="Style Template Tool", theme=_midnight_theme(), css=CUSTOM_CSS) as app:
        gr.Markdown(
            "# Style Template Tool\n\n"
            "图集风格提取  ·  Prompt 智能融合  ·  双参考图生成",
            elem_id="header-block",
        )

        # Tab 1: 风格分析
        with gr.Tab("风格分析"):
            with gr.Row(equal_height=False):
                with gr.Column(scale=2):
                    upload_images = gr.File(label="上传参考图集（1~30 张）", file_count="multiple", file_types=["image"])
                    with gr.Row():
                        detailed_check = gr.Checkbox(label="详细分析（逐张分类 + 主体判断）", value=True)
                        analyze_btn = gr.Button("开始分析", variant="primary")
                with gr.Column(scale=3):
                    desc_output = gr.Textbox(label="风格描述", lines=14, interactive=True, placeholder="上传图片后点击「开始分析」…")

            rep_gallery = gr.Gallery(label="代表图", columns=5, height=180, object_fit="cover")
            analysis_output = gr.Textbox(label="逐张分析", lines=8, interactive=False, elem_id="analysis-box")
            desc_hidden = gr.Textbox(visible=False)

            analyze_btn.click(fn=run_analysis, inputs=[upload_images, detailed_check], outputs=[desc_output, rep_gallery, desc_hidden, analysis_output])

        # Tab 2: 融合 & 生成
        with gr.Tab("融合 & 生成"):
            with gr.Row(equal_height=False):
                with gr.Column(scale=3):
                    tab2_desc = gr.Textbox(label="风格描述", lines=6, interactive=True, placeholder="从「风格分析」自动带入…")
                    user_prompt = gr.Textbox(label="用户 Prompt", lines=3, placeholder="描述你想要生成的画面…")
                    fuse_btn = gr.Button("融合 Prompt", variant="secondary")
                    fused_output = gr.Textbox(label="融合结果（可微调）", lines=5, interactive=True)
                with gr.Column(scale=2):
                    product_img = gr.Image(label="产品参考图（上传即启用双参考图模式）", type="filepath", height=180)
                    aspect_select = gr.Dropdown(label="宽高比", choices=["1:1", "3:4", "4:3", "16:9", "9:16", "3:2"], value="1:1")
                    gen_btn = gr.Button("生成图片", variant="primary", size="lg")
                    gen_status = gr.Textbox(label="状态", interactive=False, elem_id="gen-status")

            gen_gallery = gr.Gallery(label="生成结果", columns=3, height=420, object_fit="contain")
            desc_output.change(fn=lambda x: x, inputs=[desc_output], outputs=[tab2_desc])
            fuse_btn.click(fn=run_fusion, inputs=[tab2_desc, user_prompt], outputs=[fused_output])
            gen_btn.click(fn=run_generate, inputs=[fused_output, product_img, aspect_select], outputs=[gen_gallery, gen_status])

        # Tab 3: 智能套图
        with gr.Tab("智能套图"):
            with gr.Row(equal_height=False):
                with gr.Column(scale=2):
                    smart_refs = gr.File(label="参考图集", file_count="multiple", file_types=["image"])
                with gr.Column(scale=1):
                    smart_product = gr.Image(label="产品原图（可选）", type="filepath", height=160)
                with gr.Column(scale=1):
                    smart_name = gr.Textbox(label="产品 / 品牌名称", value="Product", lines=1)
                    smart_aspect = gr.Dropdown(label="宽高比", choices=["1:1", "3:4", "4:3", "16:9", "9:16"], value="3:4")
                    smart_btn = gr.Button("一键智能生成", variant="primary", size="lg")

            smart_log = gr.Textbox(label="生成日志", lines=12, interactive=False, elem_id="smart-log")
            smart_gallery = gr.Gallery(label="生成结果", columns=4, height=420, object_fit="contain")
            smart_desc = gr.Textbox(label="风格描述", lines=3, interactive=False)

            smart_btn.click(fn=run_smart_set, inputs=[smart_refs, smart_product, smart_name, smart_aspect], outputs=[smart_gallery, smart_log, smart_desc])

    return app


if __name__ == "__main__":
    if not config.GEMINI_API_KEY:
        print("\n  请先设置 GEMINI_API_KEY（.env 文件或环境变量）")
        print("  export GEMINI_API_KEY='your-key'\n")
        sys.exit(1)

    app = build_ui()
    app.launch(server_name="0.0.0.0", server_port=7860, share=False)
