# Style Template Tool

基于 AI 的电商产品图风格迁移工具。学习参考图集的风格，将目标产品生成风格一致的电商套图。

## ✨ 核心功能

### 1. 双参考图模式
```
风格参考图（来自模板）+ 产品参考图（用户上传）
         ↓
    生成保持产品一致性的风格化图片
```

### 2. 智能代表图提取
自动从图集中提取最具代表性的图片作为风格参考

### 3. 批量生成电商套图
6个预设场景一键生成完整套图：
1. 🎯 产品主图 - 白底产品展示
2. ✨ 功效展示图 - 数据可视化
3. 🔬 成分说明图 - 科学配方
4. 🛁 使用场景图 - 生活场景
5. 📖 品牌故事图 - 品牌背景
6. ⚖️ 对比展示图 - 前后对比

## 🚀 快速开始

### 安装依赖
```bash
pip install -r requirements.txt
```

### 批量生成套图
```bash
python3 generate_ecommerce_set.py
```

### 自定义生成
```python
from core.analyzer import analyze_images
from core.fusion import fuse_prompt
from core.generator import generate_image

# 1. 分析风格
style_images = ['style1.webp', 'style2.webp', ...]
description, rep_indices, rep_paths = analyze_images(style_images)

# 2. 融合Prompt
fused = fuse_prompt(description, "你的产品名称")

# 3. 生成（双参考图模式）
result = generate_image(
    prompt=fused,
    style_references=rep_paths,
    product_reference='your_product.jpg',
    aspect_ratio='3:4'
)
```

## 📁 项目结构

```
style-template-tool/
├── app.py                      # Gradio界面（单参考图）
├── app_v2.py                   # Gradio界面（双参考图）
├── app_simple.py               # 简化版界面
├── api.py                      # API服务
├── generate_ecommerce_set.py   # 批量生成电商套图
├── generate_cerave_final.py    # CeraVe示例
├── core/
│   ├── analyzer.py            # 图像分析
│   ├── fusion.py              # Prompt融合
│   ├── generator.py           # 图像生成（双参考图）
│   ├── design_classifier.py   # 设计分类
│   └── image_classifier.py    # 图像分类
├── frontend/                   # Next.js前端
├── prompts/                    # 提示词模板
├── outputs/                    # 生成结果
└── test-images/               # 测试图片
```

## 🎯 使用示例

### 示例：CeraVe产品 + The Ordinary风格

**输入**:
- 风格图集: The Ordinary 5张电商图
- 产品图: CeraVe SA Smoothing Cleanser

**输出**: 5张保持CeraVe产品但风格像The Ordinary的电商图

**效果**:
- ✅ CeraVe瓶身、标签、Logo保持一致
- ✅ The Ordinary风格（白色背景、极简、科学感）
- ✅ 专业电商摄影效果

## 🔧 技术栈

- **图像生成**: Google Gemini API
- **后端**: Python + FastAPI
- **前端**: Next.js + TypeScript + Tailwind CSS
- **UI组件**: shadcn/ui

## 📝 配置

创建 `.env` 文件：
```env
GEMINI_API_KEY=your_gemini_api_key
```

## ⚠️ 已知问题

Gradio界面因版本兼容性问题可能无法启动，建议：
1. 使用命令行脚本进行批量生成
2. 或降级Gradio版本到4.x

## 📄 许可证

MIT License

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

---

更多详细说明请查看 [README_V2.md](./README_V2.md)
