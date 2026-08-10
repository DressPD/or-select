"""Real LLM backends: OpenAI and Gemini generation, scoring, and judging.

Requires OPENAI_API_KEY / GOOGLE_API_KEY in the environment (see .env,
created from .env.example). Used to validate the OR-Select pipeline against
real, heterogeneous model output instead of the deterministic placeholders
in pipeline.py.

Clients are created lazily (only when a function is first called) so
importing this module never requires both providers' keys to be set.
"""

from __future__ import annotations

import os
import re
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

PROMPTS_DIR = Path(__file__).resolve().parents[1] / "prompts"
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-5.6-terra")
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-3.5-flash")

_NUMBER_RE = re.compile(r"[-+]?\d*\.?\d+")


def _parse_score(text: str) -> float:
    match = _NUMBER_RE.search(text)
    return max(0.0, min(1.0, float(match.group()))) if match else 0.5


def _load_prompt(name: str) -> str:
    return (PROMPTS_DIR / name).read_text()


@lru_cache(maxsize=1)
def _openai_client():
    from openai import OpenAI

    return OpenAI(api_key=os.environ["OPENAI_API_KEY"])


@lru_cache(maxsize=1)
def _gemini_client():
    from google import genai

    return genai.Client(api_key=os.environ["GOOGLE_API_KEY"])


def _openai_complete(prompt: str, *, seed: int | None = None) -> str:
    kwargs = {"seed": seed} if seed is not None else {}
    resp = _openai_client().chat.completions.create(
        model=OPENAI_MODEL,
        messages=[{"role": "user", "content": prompt}],
        **kwargs,
    )
    return (resp.choices[0].message.content or "").strip()


def _gemini_complete(prompt: str) -> str:
    resp = _gemini_client().models.generate_content(model=GEMINI_MODEL, contents=prompt)
    return (resp.text or "").strip()


# --- generation -------------------------------------------------------


def openai_generate(query: str, seed: int) -> str:
    return _openai_complete(query, seed=seed)


def gemini_generate(query: str, seed: int) -> str:
    # Gemini has no seed parameter; sampling variance across calls stands in
    # for the seed sweep used with OpenAI.
    return _gemini_complete(query)


# --- confidence scoring -------------------------------------------------

_CONFIDENCE_PROMPT = (
    "Query: {query}\n\nAnswer: {text}\n\n"
    "Rate your confidence that this answer is correct, as a single number "
    "between 0.0 and 1.0. Reply with only the number."
)


def openai_score(query: str, text: str) -> float:
    prompt = _CONFIDENCE_PROMPT.format(query=query, text=text)
    return _parse_score(_openai_complete(prompt))


def gemini_score(query: str, text: str) -> float:
    prompt = _CONFIDENCE_PROMPT.format(query=query, text=text)
    return _parse_score(_gemini_complete(prompt))


# --- pairwise judging -----------------------------------------------------


def _judge_prompt(query: str, text_a: str, text_b: str) -> str:
    template = _load_prompt("judge_prompt.txt")
    return template.format(query=query, text_a=text_a, text_b=text_b)


def openai_judge(query: str, text_a: str, text_b: str) -> float:
    return _parse_score(_openai_complete(_judge_prompt(query, text_a, text_b)))


def gemini_judge(query: str, text_a: str, text_b: str) -> float:
    return _parse_score(_gemini_complete(_judge_prompt(query, text_a, text_b)))
