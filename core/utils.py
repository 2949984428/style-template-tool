"""
公共工具模块
MIME 映射、图片转 Part、Gemini Client 单例、日志、自定义异常
"""

import os
import logging
from typing import Optional

from google import genai
from google.genai import types

import config

# ── MIME ──

MIME_MAP = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".webp": "image/webp",
    ".gif": "image/gif",
}


def get_mime_type(image_path: str) -> str:
    ext = os.path.splitext(image_path)[1].lower()
    return MIME_MAP.get(ext, "image/jpeg")


def read_image_bytes(image_path: str) -> tuple:
    with open(image_path, "rb") as f:
        data = f.read()
    return data, get_mime_type(image_path)


def image_to_part(image_path: str) -> types.Part:
    data, mime = read_image_bytes(image_path)
    return types.Part.from_bytes(data=data, mime_type=mime)


# ── Gemini Client 单例 ──

_client: Optional[genai.Client] = None


def get_client() -> genai.Client:
    global _client
    if _client is None:
        _client = genai.Client(api_key=config.GEMINI_API_KEY)
    return _client


# ── 日志 ──

LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
LOG_DATE_FORMAT = "%H:%M:%S"


def setup_logging(level: int = logging.INFO) -> None:
    logging.basicConfig(format=LOG_FORMAT, datefmt=LOG_DATE_FORMAT, level=level)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)


# ── 自定义异常 ──

class StyleToolError(Exception):
    pass

class AnalysisError(StyleToolError):
    pass

class FusionError(StyleToolError):
    pass

class GenerationError(StyleToolError):
    pass

class ConfigError(StyleToolError):
    pass
