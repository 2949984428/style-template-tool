# 风格模板自动化工具 V2

## 核心优化

### 1. 双参考图模式

```
风格参考图（来自模板）+ 产品参考图（用户上传）
         ↓
    生成保持产品一致性的风格化图片
```

**代码实现**:
```python
from core.generator import generate_image

result_paths = generate_image(
    prompt=fused_prompt,
    style_references=rep_paths,      # 风格参考图（The Ordinary风格）
    product_reference=product_ref,    # 产品参考图（CeraVe产品）
    aspect_ratio='3:4',
)
```

### 2. 代表图（keyReference）

```python
# 分析图集时自动提取代表图
description, rep_indices, rep_paths = analyze_images(images)
# rep_paths: 最具代表性的图片路径，用于风格参考
```

### 3. 批量生成套图

**电商场景预设**（6个场景）:
1. 🎯 产品主图 - 白底产品展示
2. ✨ 功效展示图 - 数据可视化
3. 🔬 成分说明图 - 科学配方
4. 🛁 使用场景图 - 生活场景
5. 📖 品牌故事图 - 品牌背景
6. ⚖️ 对比展示图 - 前后对比

**使用方法**:
```bash
python3 generate_ecommerce_set.py
```

## 文件结构

```
style-template-tool/
├── app.py                      # 原版界面
├── app_v2.py                   # 新版界面（Gradio版本问题待修复）
├── app_simple.py               # 简化版界面
├── generate_cerave_final.py    # CeraVe批量生成示例
├── generate_ecommerce_set.py   # 通用批量生成
├── core/
│   ├── analyzer.py            # ✅ 已优化（返回代表图路径）
│   ├── fusion.py              # Prompt融合
│   └── generator.py           # ✅ 已优化（双参考图模式）
├── outputs/                    # 生成结果
└── README_V2.md               # 本文档
```

## 使用示例

### 示例1: 单图生成

```python
from core.analyzer import analyze_images
from core.fusion import fuse_prompt
from core.generator import generate_image

# 1. 分析风格
style_images = ['style1.webp', 'style2.webp', ...]
description, rep_indices, rep_paths = analyze_images(style_images)

# 2. 融合Prompt
fused = fuse_prompt(description, "CeraVe洁面产品")

# 3. 生成（双参考图模式）
result = generate_image(
    prompt=fused,
    style_references=rep_paths,
    product_reference='cerave.jpg',
    aspect_ratio='3:4'
)
```

### 示例2: 批量生成套图

```bash
# 运行批量生成脚本
python3 generate_cerave_final.py

# 输出：
# - cerave_01_产品主图.png
# - cerave_02_功效展示图.png
# - cerave_03_成分说明图.png
# - cerave_04_使用场景图.png
# - cerave_05_品牌故事图.png
```

## 核心改进对比

| 功能 | V1 | V2 |
|------|----|----|
| 参考图模式 | 单参考图 | ✅ 双参考图（风格+产品） |
| 代表图提取 | 仅返回索引 | ✅ 返回路径，直接使用 |
| 批量生成 | 无 | ✅ 6场景批量生成 |
| 产品一致性 | 一般 | ✅ 保持产品不变 |
| 风格学习 | 基础 | ✅ 深度学习代表图 |

## 实际应用效果

**输入**:
- 风格图集: The Ordinary 5张电商图
- 产品图: CeraVe SA Smoothing Cleanser

**输出**: 5张保持CeraVe产品但风格像The Ordinary的电商图

**效果验证**:
- ✅ CeraVe瓶身、标签、Logo保持一致
- ✅ The Ordinary风格（白色背景、极简、科学感）
- ✅ 专业电商摄影效果

## 待修复问题

Gradio界面因版本兼容性问题暂时无法启动，建议：
1. 使用命令行脚本进行批量生成
2. 或降级Gradio版本到4.x
3. 或使用原版app.py（单参考图模式）

## 技术亮点

1. **双参考图分离**: 风格参考和产品参考分离，实现"换风格不换产品"
2. **代表图智能选择**: 自动选择最具代表性的图片作为风格参考
3. **批量场景预设**: 6个电商场景一键生成完整套图
4. **Gemini最佳实践**: 遵循官方推荐的多参考图API调用方式
