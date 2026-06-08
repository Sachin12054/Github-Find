"""
=============================================================================
 ai_reviewer.py — AI Review Engine (Gemini API Integration)
=============================================================================
 Sends extracted C# code diffs to Google Gemini for architectural review.
 The LLM acts as a senior enterprise C# architect and returns structured
 JSON feedback covering SOLID, null handling, async, security, and more.
=============================================================================
"""

import json
import os
import re
from typing import List, Dict, Any

import google.generativeai as genai


# ---------------------------------------------------------------------------
# System prompt — the "persona" and instructions for the LLM
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """You are an expert senior enterprise C# software engineer and architect with 15+ years of experience in .NET development, clean architecture, and enterprise-grade code reviews.

You are reviewing a GitHub Pull Request. Your job is to analyze the changed C# code and provide a thorough, professional code review.

## Review Checklist

Analyze the code for ALL of the following categories:

1. **SOLID Principle Violations**
   - Single Responsibility: Does a class/method do too much?
   - Open/Closed: Is the code open for extension but closed for modification?
   - Liskov Substitution: Are subtypes properly substitutable?
   - Interface Segregation: Are interfaces focused and minimal?
   - Dependency Inversion: Are high-level modules depending on abstractions?

2. **Null Reference Risks**
   - Missing null checks on parameters, return values, or collection access.
   - Potential NullReferenceException paths.
   - Nullable reference type misuse.

3. **Exception Handling Issues**
   - Empty catch blocks or swallowing exceptions.
   - Catching overly broad exception types (e.g., `catch (Exception)`).
   - Missing `finally` or `using` for disposable resources.
   - Throwing `Exception` instead of specific exception types.

4. **Async/Await Mistakes**
   - Methods marked `async` but missing `await`.
   - Using `.Result` or `.Wait()` (sync-over-async anti-pattern).
   - Missing `ConfigureAwait(false)` in library code.
   - Fire-and-forget tasks without error handling.

5. **Performance Issues**
   - Unnecessary allocations in hot paths.
   - String concatenation in loops (should use `StringBuilder`).
   - LINQ misuse leading to multiple enumerations.
   - Missing `IDisposable` implementation.

6. **Security Concerns**
   - SQL injection vulnerabilities.
   - Hardcoded secrets or connection strings.
   - Missing input validation.
   - Improper authentication/authorization checks.

7. **Code Quality & Best Practices**
   - Naming convention violations.
   - Magic numbers or strings.
   - Dead code or commented-out code.
   - Missing XML documentation on public APIs.
   - Overly complex methods (high cyclomatic complexity).

## Response Format

You MUST return a valid JSON object with exactly this structure:

```json
{
  "summary": {
    "files_reviewed": <number>,
    "total_issues": <number>,
    "critical": <number>,
    "high": <number>,
    "medium": <number>,
    "low": <number>,
    "score": <number 0-100>
  },
  "issues": [
    {
      "file": "<filename>",
      "line": <line_number>,
      "severity": "Critical|High|Medium|Low",
      "category": "<category name>",
      "issue": "<clear description of the problem>",
      "fix": "<specific actionable fix suggestion>",
      "code_before": "<problematic code snippet if applicable>",
      "code_after": "<suggested fixed code snippet if applicable>"
    }
  ]
}
```

## Important Rules

- Return ONLY the JSON object. No markdown fences, no explanations outside JSON.
- Every issue MUST have a concrete fix suggestion, not just "consider fixing".
- Line numbers must reference the NEW file line numbers shown in the diff.
- If the code is clean and has no issues, return the JSON with an empty issues array and score of 95-100.
- Be strict but fair. Do not invent problems that don't exist.
- Focus on the CHANGED lines (lines prefixed with +), but consider surrounding context.
- The `score` field should be 0-100 representing overall code quality.
"""


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def review_code(diff_text: str, file_count: int) -> Dict[str, Any]:
    """
    Send the C# diff to Google Gemini and return structured review JSON.

    Parameters
    ----------
    diff_text : str
        Formatted diff output from `format_diff_for_prompt()`.
    file_count : int
        Number of C# files being reviewed.

    Returns
    -------
    dict
        Parsed JSON review result with 'summary' and 'issues' keys.
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "GEMINI_API_KEY environment variable is not set. "
            "Please add it as a GitHub secret."
        )

    # Configure the Gemini client
    genai.configure(api_key=api_key)

    model = genai.GenerativeModel(
        model_name="gemini-2.0-flash",
        system_instruction=SYSTEM_PROMPT,
    )

    # To reduce token usage and avoid hitting free-tier quotas, send a
    # reduced version of the diff to the model:
    # - prefer added lines only (+)
    # - keep file headers for context
    # - limit total characters to a conservative size
    def _shrink_diff(text: str, max_chars: int = 2000, max_added_per_file: int = 200):
        sections: List[str] = []
        current_file = None
        added_count = 0
        for line in text.splitlines():
            # Preserve file header lines so the model knows which file the code came from
            if line.strip().startswith("═══ File:"):
                current_file = line
                added_count = 0
                sections.append(line)
                continue

            # Keep only lines that represent additions (contain '+ ' after the line number)
            # The formatted diff lines look like: 'L  12 + code...'
            if "+ " in line:
                # enforce per-file limit
                if added_count < max_added_per_file:
                    sections.append(line)
                    added_count += 1

            # Stop if we've reached max size
            if sum(len(s) for s in sections) > max_chars:
                break

        # If we couldn't find any added lines (very small diffs), fall back to original
        out = "\n".join(sections).strip()
        return out if out else text[:max_chars]

    trimmed_diff = _shrink_diff(diff_text, max_chars=2000, max_added_per_file=200)

    user_prompt = f"""## Pull Request Code Changes

The following diff shows {file_count} changed C# file(s). Only added lines are included for token efficiency.

```
{trimmed_diff}
```

Please review this code and return your analysis as JSON.
"""

    # Call Gemini
        # Reduce max_output_tokens to lower cost and token usage in CI
        response = model.generate_content(
            user_prompt,
            generation_config=genai.GenerationConfig(
                temperature=0.2,  # Low temp for deterministic review
                max_output_tokens=1024,
            ),
        )

    raw_text = response.text.strip()

    # Parse the JSON from the response
    review = _extract_json(raw_text)

    # Validate / fill defaults
    review = _validate_review(review, file_count)

    return review


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _extract_json(text: str) -> Dict[str, Any]:
    """
    Robustly extract JSON from the LLM response, handling markdown fences
    and other wrapper text.
    """
    # Try direct parse first
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Try to find JSON inside markdown code fences
    patterns = [
        r"```json\s*(.*?)\s*```",
        r"```\s*(.*?)\s*```",
        r"\{.*\}",
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1) if match.lastindex else match.group(0))
            except json.JSONDecodeError:
                continue

    # Fallback: return a default error review
    return {
        "summary": {
            "files_reviewed": 0,
            "total_issues": 1,
            "critical": 0,
            "high": 0,
            "medium": 1,
            "low": 0,
            "score": 0,
        },
        "issues": [
            {
                "file": "N/A",
                "line": 0,
                "severity": "Medium",
                "category": "AI Response Error",
                "issue": "The AI reviewer could not parse its own response. Raw output has been logged.",
                "fix": "Re-run the review or check Gemini API configuration.",
                "code_before": "",
                "code_after": "",
            }
        ],
    }


def _validate_review(review: Dict[str, Any], file_count: int) -> Dict[str, Any]:
    """Ensure all required keys exist with sensible defaults."""
    # Ensure summary exists
    if "summary" not in review:
        review["summary"] = {}

    s = review["summary"]
    s.setdefault("files_reviewed", file_count)
    s.setdefault("total_issues", len(review.get("issues", [])))
    s.setdefault("critical", 0)
    s.setdefault("high", 0)
    s.setdefault("medium", 0)
    s.setdefault("low", 0)
    s.setdefault("score", 50)

    # Ensure issues is a list
    if "issues" not in review or not isinstance(review["issues"], list):
        review["issues"] = []

    # Validate each issue
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
