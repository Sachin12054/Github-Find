"""
=============================================================================
 diff_parser.py — Code Patch Extraction Module
=============================================================================
 Reads the GitHub PR diff via the GitHub REST API and extracts only the
 changed C# (.cs) files and their hunks.  Non-C# files are filtered out
 to save AI token costs.
=============================================================================
"""

import os
import requests
from dataclasses import dataclass, field
from typing import List, Optional


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------

@dataclass
class ChangedLine:
    """Represents a single changed line in a diff hunk."""
    line_number: int          # Line number in the NEW file
    content: str              # The raw line text (without +/- prefix)
    change_type: str          # 'added', 'deleted', or 'context'


@dataclass
class DiffHunk:
    """A contiguous hunk of changes inside a file."""
    start_line: int           # Starting line in the new file
    end_line: int             # Ending line in the new file
    lines: List[ChangedLine] = field(default_factory=list)


@dataclass
class ChangedFile:
    """A single C# file that was modified in the PR."""
    filename: str
    status: str               # 'added', 'modified', 'removed', 'renamed'
    patch: str                # Raw unified-diff patch text
    hunks: List[DiffHunk] = field(default_factory=list)
    additions: int = 0
    deletions: int = 0


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def get_pr_changed_files(
    repo: str,
    pr_number: int,
    github_token: str,
) -> List[ChangedFile]:
    """
    Fetch files changed in a Pull Request and return only C# files
    with their parsed diff hunks.

    Parameters
    ----------
    repo : str
        Full repository name, e.g. "owner/repo".
    pr_number : int
        The pull-request number.
    github_token : str
        A GitHub token with `pull-requests: read` scope.

    Returns
    -------
    list[ChangedFile]
        Only `.cs` files with parsed hunks.
    """
    url = f"https://api.github.com/repos/{repo}/pulls/{pr_number}/files"
    headers = {
        "Authorization": f"Bearer {github_token}",
        "Accept": "application/vnd.github.v3+json",
    }

    all_files: List[ChangedFile] = []
    page = 1

    while True:
        resp = requests.get(url, headers=headers, params={"per_page": 100, "page": page})
        resp.raise_for_status()
        files_data = resp.json()

        if not files_data:
            break

        for f in files_data:
            filename = f.get("filename", "")

            # ── FILTER: only C# source files ──
            if not filename.endswith(".cs"):
                continue

            patch = f.get("patch", "")
            if not patch:
                continue

            changed = ChangedFile(
                filename=filename,
                status=f.get("status", "modified"),
                patch=patch,
                additions=f.get("additions", 0),
                deletions=f.get("deletions", 0),
            )
            changed.hunks = _parse_patch(patch)
            all_files.append(changed)

        page += 1

    return all_files


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _parse_patch(patch: str) -> List[DiffHunk]:
    """Parse a unified-diff patch string into a list of DiffHunk objects."""
    hunks: List[DiffHunk] = []
    current_hunk: Optional[DiffHunk] = None
    new_line_num = 0

    for raw_line in patch.split("\n"):
        # Hunk header: @@ -old_start,old_count +new_start,new_count @@
        if raw_line.startswith("@@"):
            # Extract new-file start line
            try:
                parts = raw_line.split("+")[1].split("@@")[0].strip()
                if "," in parts:
                    start = int(parts.split(",")[0])
                else:
                    start = int(parts)
            except (IndexError, ValueError):
                start = 1

            current_hunk = DiffHunk(start_line=start, end_line=start)
            new_line_num = start
            hunks.append(current_hunk)
            continue

        if current_hunk is None:
            continue

        if raw_line.startswith("+"):
            current_hunk.lines.append(
                ChangedLine(
                    line_number=new_line_num,
                    content=raw_line[1:],
                    change_type="added",
                )
            )
            current_hunk.end_line = new_line_num
            new_line_num += 1

        elif raw_line.startswith("-"):
            current_hunk.lines.append(
                ChangedLine(
                    line_number=new_line_num,
                    content=raw_line[1:],
                    change_type="deleted",
                )
            )
            # Deleted lines do NOT advance the new-file line counter

        else:
            # Context line (unchanged)
            current_hunk.lines.append(
                ChangedLine(
                    line_number=new_line_num,
                    content=raw_line,
                    change_type="context",
                )
            )
            current_hunk.end_line = new_line_num
            new_line_num += 1

    return hunks


def format_diff_for_prompt(files: List[ChangedFile]) -> str:
    """
    Build a human-readable representation of the changed C# code
    suitable for inclusion in an LLM prompt.
    """
    sections: List[str] = []
    for f in files:
        header = f"═══ File: {f.filename} ({f.status}) ═══"
        sections.append(header)
        for hunk in f.hunks:
            for line in hunk.lines:
                prefix = {"added": "+ ", "deleted": "- ", "context": "  "}.get(
                    line.change_type, "  "
                )
                sections.append(f"L{line.line_number:>4} {prefix}{line.content}")
        sections.append("")   # blank separator

    return "\n".join(sections)
