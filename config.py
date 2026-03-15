import os

# 手动加载 .env 文件
def _load_env():
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    os.environ.setdefault(key.strip(), value.strip())

_load_env()

# Gemini API 配置
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

# 模型配置
ANALYSIS_MODEL = "gemini-2.0-flash"   # 图集分析（多模态文本）
FUSION_MODEL = "gemini-2.0-flash"     # prompt 融合（文本）
IMAGE_MODEL = "gemini-3.1-flash-image-preview"  # 图片生成（支持图片输出）

# 输出目录
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "outputs")

# 图集限制
MAX_IMAGES = 30
MAX_IMAGE_SIZE_MB = 10

# 图片生成参数
DEFAULT_ASPECT_RATIO = "1:1"
DEFAULT_IMAGE_SIZE = "1K"
