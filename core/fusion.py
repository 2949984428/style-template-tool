"""
Stage 2: Prompt Fusion via LLM
Uses Gemini to generate a flowing, natural image generation prompt
based on style analysis, content intent, and exclusion rules.
"""

import os
from pathlib import Path
from google import genai

from core.utils import get_logger, FusionError

logger = get_logger("fusion")

_TEMPLATE_PATH = Path(__file__).parent.parent / "prompts" / "fusion.txt"
_MODEL = os.getenv("FUSION_MODEL", "gemini-2.5-flash")


def _load_template() -> str:
    with open(_TEMPLATE_PATH, "r", encoding="utf-8") as f:
        return f.read()


def _build_ref_range(ref_count: int) -> tuple[str, str]:
    """Generate reference range strings for the template."""
    if ref_count <= 1:
        return ("", "")
    last = ref_count + 1  # +1 because product is Image 1
    return (f"-{last}", f", Reference Image 3" + (f"...Reference Image {last}" if ref_count > 2 else ""))


def fuse_prompt(
    template_description: str,
    user_prompt: str,
    ref_count: int = 1,
    product_description: str = "",
    exclude_items: str = "",
    style_info: dict = None,
) -> str:
    """
    Call LLM to produce a single flowing image generation prompt.

    Args:
        template_description: style analysis text
        user_prompt: content intent
        ref_count: number of style reference images
        product_description: product appearance (optional)
        exclude_items: elements to exclude
        style_info: overall_style dict (unused now, kept for interface compat)
    """
    if not user_prompt.strip():
        raise FusionError("user_prompt cannot be empty")

    template = _load_template()
    ref_range, ref_range_repeat = _build_ref_range(ref_count)

    system_prompt = template.replace(
        "{template_description}", template_description
    ).replace(
        "{user_prompt}", user_prompt
    ).replace(
        "{product_description}", product_description or "(not provided — the model should read product details directly from Reference Image 1)"
    ).replace(
        "{exclude_items}", exclude_items or "any brand names, logos, text from style references"
    ).replace(
        "{ref_range}", ref_range
    ).replace(
        "{ref_range_repeat}", ref_range_repeat
    )

    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

    for attempt in range(3):
        response = client.models.generate_content(
            model=_MODEL,
            contents=system_prompt,
            config={
                "temperature": 0.7,
                "max_output_tokens": 2048,
            },
        )
        result = response.text.strip().strip('"').strip()
        word_count = len(result.split())
        logger.info("Attempt %d: %d words", attempt + 1, word_count)

        if word_count >= 150:
            logger.info("Fusion complete: %d words", word_count)
            return result

        logger.warning("Too short (%d words), retrying...", word_count)

    logger.warning("All retries exhausted, using last result (%d words)", word_count)
    return result
