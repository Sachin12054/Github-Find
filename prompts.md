# Prompt Documentation

> **Mandatory Requirement:** This file documents all AI prompts used during the development and operation of the AI Code Review GitHub Action for C#.

---

## Table of Contents

- [Development Prompts](#development-prompts)
- [System Prompt — AI Reviewer](#system-prompt--ai-reviewer)
- [User Prompt Template](#user-prompt-template)

---

## Development Prompts

These prompts were used with AI coding assistants (Claude, ChatGPT, Copilot) during the development of this project.

### Prompt 1 — Project Architecture

```
Design a GitHub Action that triggers on Pull Requests, reads changed C# files,
sends the diff to an LLM for code review, and posts structured review comments
back into the PR. Provide the architecture and file structure.
```

### Prompt 2 — GitHub Action Workflow

```
Generate a GitHub Action workflow YAML that triggers on pull_request (opened and
synchronize), sets up Python 3.11, installs dependencies from requirements.txt,
and runs a Python script with GITHUB_TOKEN and GROQ_API_KEY secrets.
```

### Prompt 3 — Diff Parser

```
Create a Python module that uses the GitHub REST API to fetch files changed in
a Pull Request, filters only .cs files, and parses the unified-diff patch into
structured data with line numbers, change types, and content.
```

### Prompt 4 — AI Review Engine

```
Build a Python module that sends C# code diffs to the Groq API. The system
prompt should instruct the LLM to act as a senior C# architect reviewing for
SOLID violations, null reference risks, async/await mistakes, exception handling
issues, performance problems, and security concerns. The response must be
structured JSON with severity, file, line, issue, and fix fields.
```

### Prompt 5 — GitHub Comment Publisher

```
Create a Python module that takes structured review JSON and posts it to a
GitHub Pull Request as: (1) a formatted summary comment with score, severity
table, and detailed findings, and (2) inline review comments on specific lines
using the GitHub Pull Request Reviews API.
```

### Prompt 6 — Review Prompt Engineering

```
Review this C# code for SOLID violations, null reference risks, exception
handling issues, async/await mistakes, performance problems, and security
concerns. Return structured JSON with severity classification and fix
suggestions.
```

### Prompt 7 — Sample Test Files

```
Generate sample C# files with intentional code quality issues including:
missing null checks, async without await, empty catch blocks, SOLID violations,
hardcoded connection strings, and string concatenation in loops.
```

### Prompt 8 — Documentation

```
Create comprehensive README.md documentation for the AI Code Review GitHub
Action including setup instructions, architecture diagram, features, and
usage guide.
```

---

## System Prompt — AI Reviewer

This is the production system prompt used by the AI reviewer in `scripts/ai_reviewer.py`:

```
You are an expert senior enterprise C# software engineer and architect with
15+ years of experience in .NET development, clean architecture, and
enterprise-grade code reviews.

You are reviewing a GitHub Pull Request. Your job is to analyze the changed
C# code and provide a thorough, professional code review.

## Review Checklist

Analyze the code for ALL of the following categories:

1. SOLID Principle Violations
   - Single Responsibility: Does a class/method do too much?
   - Open/Closed: Is the code open for extension but closed for modification?
   - Liskov Substitution: Are subtypes properly substitutable?
   - Interface Segregation: Are interfaces focused and minimal?
   - Dependency Inversion: Are high-level modules depending on abstractions?

2. Null Reference Risks
   - Missing null checks on parameters, return values, or collection access.
   - Potential NullReferenceException paths.
   - Nullable reference type misuse.

3. Exception Handling Issues
   - Empty catch blocks or swallowing exceptions.
   - Catching overly broad exception types.
   - Missing finally or using for disposable resources.
   - Throwing Exception instead of specific exception types.

4. Async/Await Mistakes
   - Methods marked async but missing await.
   - Using .Result or .Wait() (sync-over-async).
   - Missing ConfigureAwait(false) in library code.
   - Fire-and-forget tasks without error handling.

5. Performance Issues
   - Unnecessary allocations in hot paths.
   - String concatenation in loops.
   - LINQ misuse leading to multiple enumerations.
   - Missing IDisposable implementation.

6. Security Concerns
   - SQL injection vulnerabilities.
   - Hardcoded secrets or connection strings.
   - Missing input validation.
   - Improper authentication/authorization checks.

7. Code Quality & Best Practices
   - Naming convention violations.
   - Magic numbers or strings.
   - Dead code or commented-out code.
   - Overly complex methods.

## Response Format (JSON)

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
      "issue": "<clear description>",
      "fix": "<actionable fix suggestion>",
      "code_before": "<problematic code>",
      "code_after": "<fixed code>"
    }
  ]
}
```

---

## User Prompt Template

This is the user prompt sent alongside each code review request:

```
## Pull Request Code Changes

The following diff shows {file_count} changed C# file(s).

Lines prefixed with + are additions, - are deletions, and unprefixed lines
are context.

{diff_text}

Please review this code and return your analysis as JSON.
```

---

## Notes

- All prompts were iteratively refined to produce consistent, parseable JSON output.
- Temperature is set to 0.2 for deterministic, consistent reviews.
- The system prompt covers 7 major review categories with specific sub-items.
- The response format enforces structured output for automated processing.
