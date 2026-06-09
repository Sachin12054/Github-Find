"""
=============================================================================
 test_local.py — Local Testing Script
=============================================================================
 Run this script locally to test the AI review on the sample C# files
 without needing a real GitHub PR. Requires GROQ_API_KEY env var.
 
 Usage:
     set GROQ_API_KEY=your-key-here
   python test_local.py
=============================================================================
"""

import os
import sys
import json

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from scripts.ai_reviewer import review_code


def main():
    if not os.environ.get("GROQ_API_KEY"):
        print("[ERROR] Please set GROQ_API_KEY environment variable.")
        print("   Example: set GROQ_API_KEY=your-key-here")
        sys.exit(1)

    # Read sample files
    samples_dir = os.path.join(os.path.dirname(__file__), "samples")
    diff_parts = []
    file_count = 0

    for fname in os.listdir(samples_dir):
        if not fname.endswith(".cs"):
            continue
        filepath = os.path.join(samples_dir, fname)
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        file_count += 1
        diff_parts.append(f"═══ File: {fname} (added) ═══")
        for i, line in enumerate(content.split("\n"), 1):
            diff_parts.append(f"L{i:>4} + {line}")
        diff_parts.append("")

    diff_text = "\n".join(diff_parts)

    print("=" * 60)
    print("AI Code Review -- Local Test Mode")
    print("=" * 60)
    print(f"Files: {file_count}")
    print(f"Diff size: {len(diff_text)} chars")
    print("\nSending to Groq...\n")

    review = review_code(diff_text, file_count)

    # Pretty print
    print(json.dumps(review, indent=2))

    # Summary
    s = review.get("summary", {})
    print(f"\n{'=' * 60}")
    print(f"Score: {s.get('score', 'N/A')} / 100")
    print(f"Issues: {s.get('total_issues', 0)}")
    print(f"   Critical: {s.get('critical', 0)}")
    print(f"   High: {s.get('high', 0)}")
    print(f"   Medium: {s.get('medium', 0)}")
    print(f"   Low: {s.get('low', 0)}")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
