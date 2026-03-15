import os


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

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

# 模型配置
ANALYSIS_MODEL = "gemini-2.5-flash"
FUSION_MODEL = "gemini-2.5-flash"
IMAGE_MODEL = "gemini-2.5-flash-image"

# 输出目录
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "outputs")

# 图集限制
MAX_IMAGES = 30
MAX_IMAGE_SIZE_MB = 10

# 图片生成参数
DEFAULT_ASPECT_RATIO = "1:1"
DEFAULT_IMAGE_SIZE = "1K"
