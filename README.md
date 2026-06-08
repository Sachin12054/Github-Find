# AI Code Review GitHub Action for C#

> Automated AI-powered code review system that triggers on GitHub Pull Requests, analyzes changed C# code using Google Gemini, and posts structured review feedback directly into the PR.

[![GitHub Actions](https://img.shields.io/badge/GitHub_Actions-2088FF?style=for-the-badge&logo=github-actions&logoColor=white)](https://github.com/features/actions)
[![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Google Gemini](https://img.shields.io/badge/Google_Gemini-8E75B2?style=for-the-badge&logo=google&logoColor=white)](https://ai.google.dev/)

---

## Table of Contents

- [Problem Statement](#problem-statement)
- [Solution](#solution)
- [Architecture](#architecture)
- [Features](#features)
- [Setup Guide](#setup-guide)
- [How It Works](#how-it-works)
- [Project Structure](#project-structure)
- [Demo](#demo)
- [AI Capabilities](#ai-capabilities-demonstrated)
- [Tech Stack](#tech-stack)

---

## Problem Statement

| Current State | Impact |
|---|---|
| Developers submit Pull Requests | Reviews take hours or days |
| Senior engineers manually review | Human reviewers miss issues |
| No automated quality gates | Bugs slip into production |
| Inconsistent review standards | Code quality varies |

---

## Solution

An **AI-powered automated code reviewer** that:

1. **Detects** when a PR is created or updated
2. **Reads** changed C# files from the PR diff
3. **Sends** code to Google Gemini for expert review
4. **Generates** structured feedback with severity & fix suggestions
5. **Posts** review comments directly into the GitHub PR

```
GitHub PR --> GitHub Action --> Extract Diff --> AI Review --> PR Comments
```

---

## Architecture

```
+----------------+
|   Developer    |
|   Opens PR     |
+-------+--------+
        |
        v
+-------------------------------+
|  GitHub Action Trigger        |
|  (.github/workflows/review.yml)  |
+-------+-----------------------+
        |
        v
+-------------------------------+
|  Phase 1: Extract Diff        |
|  (scripts/diff_parser.py)     |
|  - Fetch PR changed files     |
|  - Filter only *.cs files     |
|  - Parse unified-diff hunks   |
+-------+-----------------------+
        |
        v
+-------------------------------+
|  Phase 2: AI Review           |
|  (scripts/ai_reviewer.py)     |
|  - Send diff to Gemini API    |
|  - System prompt: C# expert   |
|  - Get structured JSON back   |
+-------+-----------------------+
        |
        v
+-------------------------------+
|  Phase 3: Post Comments       |
|  (scripts/github_commenter.py)|
|  - Format Markdown summary    |
|  - Post PR summary comment    |
|  - Post inline line comments  |
+-------------------------------+
```

---

## Features

### Core Features
- **Automatic PR Trigger** -- Runs on PR open & update
- **C# File Filtering** -- Only reviews `.cs` files (saves tokens)
- **AI-Powered Review** -- Google Gemini as senior C# architect
- **Structured JSON Output** -- Parseable, consistent results
- **PR Comments** -- Summary + inline comments posted automatically

### Review Categories
- SOLID Principle Violations
- Null Reference Risks
- Exception Handling Issues
- Async/Await Mistakes
- Performance Problems
- Security Concerns
- Code Quality & Best Practices

### Bonus Features
- **Severity Classification** -- Critical / High / Medium / Low
- **Code Quality Score** -- 0-100 rating per PR
- **Fix Suggestions** -- Concrete code fixes, not just complaints
- **Before/After Code** -- Shows problematic vs. fixed code
- **Review Summary Table** -- At-a-glance issue breakdown

---

## Setup Guide

### Prerequisites

- A GitHub repository with C# code
- A Google Gemini API key (free tier available)

### Step 1: Get a Gemini API Key

1. Go to [Google AI Studio](https://aistudio.google.com/apikey)
2. Click **"Create API Key"**
3. Copy the key

### Step 2: Add GitHub Secret

1. Go to your GitHub repository -> **Settings** -> **Secrets and variables** -> **Actions**
2. Click **"New repository secret"**
3. Name: `GEMINI_API_KEY`
4. Value: paste your Gemini API key
5. Click **"Add secret"**

> **Note:** `GITHUB_TOKEN` is automatically provided by GitHub Actions -- no setup needed.

### Step 3: Add Project Files

Copy these files into your repository:

```
your-repo/
|-- .github/
|   +-- workflows/
|       +-- review.yml          <-- GitHub Action workflow
|-- scripts/
|   |-- __init__.py
|   |-- review.py               <-- Main orchestrator
|   |-- diff_parser.py          <-- Diff extraction
|   |-- ai_reviewer.py          <-- Gemini AI integration
|   +-- github_commenter.py     <-- PR comment publisher
|-- requirements.txt            <-- Python dependencies
+-- prompts.md                  <-- Prompt documentation
```

### Step 4: Push & Create a PR

```bash
git add .
git commit -m "Add AI code review action"
git push origin main
```

Then create a branch, modify a `.cs` file, and open a Pull Request. The AI reviewer will automatically run!

---

## How It Works

### End-to-End Flow

```
1. Developer opens/updates PR with C# changes
       |
2. GitHub Action triggers (review.yml)
       |
3. diff_parser.py fetches PR files via GitHub API
       |
4. Filters only .cs files, parses unified-diff patches
       |
5. ai_reviewer.py sends formatted diff to Gemini
       |
6. Gemini returns structured JSON review
       |
7. github_commenter.py posts:
   - Summary comment (score, table, detailed findings)
   - Inline comments on specific lines
       |
8. Developer sees review in PR conversation [DONE]
```

### Example Output

The AI reviewer posts a comment like this:

```
# AI Code Review Results

## Code Quality Score
### [WARN] 62 / 100 -- Needs Improvement

## Review Summary
| Metric          | Value |
|-----------------|-------|
| Files Reviewed  | 2     |
| Total Issues    | 7     |
| Critical        | 1     |
| High            | 2     |
| Medium          | 3     |
| Low             | 1     |

## Detailed Findings

### [!] Issue #1 -- CRITICAL | Security
File: UserService.cs | Line: 20
Problem: Hardcoded connection string with plaintext password
Fix: Use environment variables or Azure Key Vault
```

---

## Project Structure

```
ai-code-review/
|
|-- .github/
|   +-- workflows/
|       +-- review.yml              # GitHub Action workflow definition
|
|-- scripts/
|   |-- __init__.py                 # Python package marker
|   |-- review.py                   # Main orchestrator (entry point)
|   |-- diff_parser.py              # PR diff extraction & C# filtering
|   |-- ai_reviewer.py              # Gemini AI integration & review engine
|   +-- github_commenter.py         # GitHub PR comment publisher
|
|-- samples/
|   |-- UserService.cs              # Sample C# with intentional issues
|   +-- OrderService.cs             # Sample C# with intentional issues
|
|-- .gitignore                      # Git ignore rules
|-- requirements.txt                # Python dependencies
|-- prompts.md                      # Prompt documentation (mandatory)
+-- README.md                       # This file
```

---

## AI Capabilities Demonstrated

### Capability: External API / Service Integration

This project demonstrates **External API Integration** as the mandatory AI capability:

| API | Purpose |
|-----|---------|
| **Google Gemini API** | AI-powered code analysis and review generation |
| **GitHub REST API** | Fetch PR diffs, post comments, create reviews |

### How AI is Used

1. **Development:** AI assistants (Claude/Copilot) used to build the project
2. **Runtime:** Gemini API analyzes C# code and generates structured reviews
3. **Prompt Engineering:** Carefully crafted system prompt ensures consistent, professional output

---

## Tech Stack

| Component | Technology |
|-----------|------------|
| **CI/CD** | GitHub Actions |
| **Language** | Python 3.11 |
| **AI Model** | Google Gemini 2.0 Flash |
| **APIs** | GitHub REST API, Gemini API |
| **Output** | Structured JSON, Markdown |

---

## Hackathon Checklist

- [x] AI-Assisted Development (documented in prompts.md)
- [x] Prompt Documentation (prompts.md)
- [x] AI Capability: External API Integration (Gemini + GitHub API)
- [x] Working End-to-End Flow
- [x] Structured Output (JSON -> Markdown)
- [x] Severity Classification
- [x] Code Quality Score
- [x] Fix Suggestions
- [x] Clean Documentation

---

## License

MIT License -- see [LICENSE](LICENSE) for details.

---

> **Built for the AI Prototype Challenge** -- Demonstrating AI-powered DevOps workflow enhancement through automated code review.
