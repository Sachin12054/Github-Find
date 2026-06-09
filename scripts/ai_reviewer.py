"""
=============================================================================
 ai_reviewer.py — Groq-backed Review Engine
=============================================================================
 Sends changed C# code to Groq's OpenAI-compatible API and returns structured
 JSON review feedback for the GitHub PR workflow.
=============================================================================
"""

import json
import os
import re
from typing import Any, Dict, List

import requests


GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
DEFAULT_GROQ_MODEL = "llama-3.1-70b-versatile"


def review_code(diff_text: str, file_count: int) -> Dict[str, Any]:
    """Send the diff to Groq and return a validated review payload."""
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY is not configured.")

    model = os.environ.get("GROQ_MODEL", DEFAULT_GROQ_MODEL)
    payload = {
        "model": model,
        "temperature": 0.1,
        "messages": [
            {"role": "system", "content": _system_prompt()},
            {"role": "user", "content": _user_prompt(diff_text, file_count)},
        ],
    }

    response = requests.post(
        GROQ_API_URL,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=90,
    )
    response.raise_for_status()

    body = response.json()
    try:
        content = body["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise RuntimeError("Groq response did not include review content.") from exc

    review = _parse_review_json(content)
    return _validate_review(review, file_count)


def _system_prompt() -> str:
    return (
        "You are an expert senior enterprise C# software engineer and architect with "
        "15+ years of experience in .NET development, clean architecture, and "
        "enterprise-grade code reviews.\n\n"
        "Analyze the changed C# code for SOLID violations, null reference risks, "
        "exception handling issues, async/await mistakes, performance problems, "
        "and security concerns. Return ONLY valid JSON with this structure:\n\n"
        "{\n"
        '  "summary": {\n'
        '    "files_reviewed": 0,\n'
        '    "total_issues": 0,\n'
        '    "critical": 0,\n'
        '    "high": 0,\n'
        '    "medium": 0,\n'
        '    "low": 0,\n'
        '    "score": 0\n'
        "  },\n"
        '  "issues": [\n'
        "    {\n"
        '      "file": "path/to/file.cs",\n'
        '      "line": 1,\n'
        '      "severity": "Critical|High|Medium|Low",\n'
        '      "category": "Security",\n'
        '      "issue": "short description",\n'
        '      "fix": "actionable fix",\n'
        '      "code_before": "problematic code",\n'
        '      "code_after": "suggested replacement"\n'
        "    }\n"
        "  ]\n"
        "}\n\n"
        "Do not wrap the JSON in markdown fences. Keep descriptions concise and concrete."
    )


def _user_prompt(diff_text: str, file_count: int) -> str:
    return (
        f"Review {file_count} changed C# file(s) and return the JSON object exactly.\n\n"
        f"{diff_text}"
    )


def _parse_review_json(content: str) -> Dict[str, Any]:
    text = content.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)

    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1:
        text = text[start : end + 1]

    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Groq returned invalid JSON: {content}") from exc


def _validate_review(review: Dict[str, Any], file_count: int) -> Dict[str, Any]:
    if "summary" not in review or not isinstance(review["summary"], dict):
        review["summary"] = {}

    summary = review["summary"]
    summary.setdefault("files_reviewed", file_count)
    summary.setdefault("total_issues", len(review.get("issues", [])))
    summary.setdefault("critical", 0)
    summary.setdefault("high", 0)
    summary.setdefault("medium", 0)
    summary.setdefault("low", 0)
    summary.setdefault("score", 50)

    if "issues" not in review or not isinstance(review["issues"], list):
        review["issues"] = []

    for issue in review["issues"]:
        issue.setdefault("file", "Unknown")
        issue.setdefault("line", 0)
        issue.setdefault("severity", "Medium")
        issue.setdefault("category", "General")
        issue.setdefault("issue", "No description")
        issue.setdefault("fix", "No fix suggested")
        issue.setdefault("code_before", "")
        issue.setdefault("code_after", "")

    return review
