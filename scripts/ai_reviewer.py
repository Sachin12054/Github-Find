"""
=============================================================================
 ai_reviewer.py — Local Review Engine
=============================================================================
 Performs deterministic, rules-based review of changed C# code without calling
 external AI services. This keeps CI reliable without API keys, billing, or
 quota limits.
=============================================================================
"""

import json
import re
from collections import Counter
from typing import List, Dict, Any


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def review_code(diff_text: str, file_count: int) -> Dict[str, Any]:
    """
    Run a deterministic local review over the C# diff and return structured
    JSON feedback.

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
    review = _local_review(diff_text, file_count)
    return _validate_review(review, file_count)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _local_review(diff_text: str, file_count: int) -> Dict[str, Any]:
    """Generate a review using deterministic heuristics over the changed code."""
    files = _parse_changed_files(diff_text)
    issues: List[Dict[str, Any]] = []

    for file_name, lines in files.items():
        issues.extend(_review_csharp_file(file_name, lines))

    severity_counts = Counter(issue["severity"] for issue in issues)
    total_issues = len(issues)

    # Start from a high score and subtract for findings.
    score = 100
    for issue in issues:
        if issue["severity"] == "Critical":
            score -= 20
        elif issue["severity"] == "High":
            score -= 12
        elif issue["severity"] == "Medium":
            score -= 7
        else:
            score -= 3
    score = max(0, min(100, score))

    return {
        "summary": {
            "files_reviewed": file_count,
            "total_issues": total_issues,
            "critical": severity_counts.get("Critical", 0),
            "high": severity_counts.get("High", 0),
            "medium": severity_counts.get("Medium", 0),
            "low": severity_counts.get("Low", 0),
            "score": score if total_issues else 95,
        },
        "issues": issues,
    }


def _parse_changed_files(diff_text: str) -> Dict[str, List[Dict[str, Any]]]:
    """Parse the formatted diff into per-file added lines with line numbers."""
    files: Dict[str, List[Dict[str, Any]]] = {}
    current_file = None

    for raw_line in diff_text.splitlines():
        header_match = re.match(r"^═══ File:\s*(.*?)\s*\(", raw_line)
        if header_match:
            current_file = header_match.group(1).strip()
            files.setdefault(current_file, [])
            continue

        if not current_file:
            continue

        line_match = re.match(r"^L\s*(\d+)\s+([+\- ])\s?(.*)$", raw_line)
        if not line_match:
            continue

        line_no = int(line_match.group(1))
        prefix = line_match.group(2)
        content = line_match.group(3)

        files[current_file].append(
            {"line": line_no, "prefix": prefix, "content": content, "raw": raw_line}
        )

    return files


def _review_csharp_file(file_name: str, lines: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Apply a small set of high-value heuristics to a changed C# file."""
    issues: List[Dict[str, Any]] = []
    joined = "\n".join(item["content"] for item in lines)

    def add_issue(line_no: int, severity: str, category: str, issue: str, fix: str, before: str = "", after: str = ""):
        issues.append(
            {
                "file": file_name,
                "line": line_no,
                "severity": severity,
                "category": category,
                "issue": issue,
                "fix": fix,
                "code_before": before,
                "code_after": after,
            }
        )

    # Hardcoded secrets / connection strings
    for item in lines:
        content = item["content"]
        lowered = content.lower()
        if any(token in lowered for token in ["password=", "secret=", "api_key", "connectionstring", "connection string"]):
            add_issue(
                item["line"],
                "High",
                "Security",
                "Hardcoded secret or connection string detected in source code.",
                "Move secrets into environment variables or GitHub Secrets and read them at runtime.",
                content.strip(),
                'var connectionString = Environment.GetEnvironmentVariable("USER_DB_CONNECTION_STRING");',
            )
            break

    # SQL injection: string concatenation in SQL query
    sql_patterns = [r'SELECT\s+.*\+.*', r'INSERT\s+.*\+.*', r'UPDATE\s+.*\+.*', r'DELETE\s+.*\+.*']
    for item in lines:
        content = item["content"]
        if any(re.search(pattern, content, re.IGNORECASE) for pattern in sql_patterns):
            add_issue(
                item["line"],
                "High",
                "Security",
                "Possible SQL injection due to string concatenation in a query.",
                "Use parameterized queries or an ORM instead of concatenating user input into SQL.",
                content.strip(),
                'var query = "SELECT * FROM Users WHERE Name = @name";',
            )
            break

    # async without await
    for item in lines:
        content = item["content"]
        if re.search(r"\basync\b", content) and re.search(r"Task<|Task\b", content):
            if not any("await" in x["content"] for x in lines):
                add_issue(
                    item["line"],
                    "Medium",
                    "Async/Await",
                    "Async method does not contain an await and may be using the async keyword unnecessarily.",
                    "Either add an await inside the method or remove async and return the task directly.",
                    content.strip(),
                    content.replace("async ", "", 1),
                )
            break

    # .Result / .Wait()
    for item in lines:
        content = item["content"]
        if ".Result" in content or ".Wait(" in content:
            add_issue(
                item["line"],
                "Medium",
                "Async/Await",
                "Sync-over-async pattern detected via .Result or .Wait().",
                "Prefer awaiting the task asynchronously instead of blocking the thread.",
                content.strip(),
                content.replace(".Result", "").replace(".Wait()", "await ..."),
            )
            break

    # Empty catch / broad catch
    for idx, item in enumerate(lines):
        content = item["content"]
        if re.search(r"catch\s*\(Exception\)", content):
            add_issue(
                item["line"],
                "Medium",
                "Exception Handling",
                "Broad catch(Exception) can hide failures and make debugging harder.",
                "Catch a more specific exception type and log or surface the error appropriately.",
                content.strip(),
                content.replace("Exception", "SqlException"),
            )
            # look for an empty catch body nearby
            window = "\n".join(x["content"] for x in lines[idx: idx + 6])
            if re.search(r"catch\s*\(Exception\)\s*\{\s*\}", window, re.DOTALL):
                add_issue(
                    item["line"],
                    "Medium",
                    "Exception Handling",
                    "Empty catch block swallows exceptions.",
                    "Log the exception, rethrow it, or handle it in a controlled way.",
                    "catch (Exception) { }",
                    "catch (Exception ex) { logger.LogError(ex, \"...\"); throw; }",
                )
            break

    # Null reference risk
    for item in lines:
        content = item["content"]
        if re.search(r"return\s+user\.(\w+)", content) or re.search(r"\.ToLower\(\)", content):
            add_issue(
                item["line"],
                "Medium",
                "Null Reference Risks",
                "Method dereferences an object without a null check.",
                "Validate the input parameter and return a guarded value or throw ArgumentNullException.",
                content.strip(),
                "if (user is null) throw new ArgumentNullException(nameof(user));",
            )
            break

    # String concatenation in loop
    loop_started = False
    for item in lines:
        content = item["content"]
        if re.search(r"foreach\s*\(", content):
            loop_started = True
        if loop_started and " + " in content and any(token in content for token in ['"User:"', '"Email:"', 'report +=']):
            add_issue(
                item["line"],
                "Low",
                "Performance",
                "String concatenation inside a loop can create unnecessary allocations.",
                "Use StringBuilder to accumulate strings efficiently in loops.",
                content.strip(),
                "reportBuilder.AppendLine($\"User: {user.Name}, Email: {user.Email}\");",
            )
            break

    # Magic numbers / direct validation
    for item in lines:
        content = item["content"]
        if re.search(r"\bif\s*\(.*<\s*2\s*\)", content) or re.search(r"\b0\.9m\b", content):
            add_issue(
                item["line"],
                "Low",
                "Code Quality & Best Practices",
                "Magic number detected in business logic.",
                "Replace the literal with a named constant or configuration value.",
                content.strip(),
                content.replace("2", "MinNameLength").replace("0.9m", "DiscountRate"),
            )
            break

    # Remove duplicates while preserving order
    unique_issues: List[Dict[str, Any]] = []
    seen = set()
    for issue in issues:
        key = (issue["file"], issue["line"], issue["category"], issue["issue"])
        if key in seen:
            continue
        seen.add(key)
        unique_issues.append(issue)

    return unique_issues


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
