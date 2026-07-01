# GitHub Repo Skill: The Next Evolution of Repository Discovery

This is the next-generation version of the **GitHub Repo Finder**. While the original tool focused on discovering useful repositories, this evolved skill is a **Repository Composition Engine**. It is designed to help you build complex projects faster by discovering, evaluating, and generating blueprints to combine existing open-source tools with minimal custom code.

## 🚀 Quick Start Guide

This skill consists of two primary scripts located in the `scripts/` directory.

### 1. Find and Score Repositories
Use `repo_finder.py` to discover the best tools for any task. It automatically expands your request into multiple search queries and scores results out of 100.

```bash
# Basic search for a task
python scripts/repo_finder.py --task "AI chatbot with Next.js" --max-results 5

# Search for a specific language with a quality threshold
python scripts/repo_finder.py --task "PDF processing" --language python --min-stars 500
```

### 2. Compare Specific Repositories
When you have a few candidates and need to make a data-driven choice, use the `compare` mode.

```bash
python scripts/repo_finder.py --mode compare --repos "owner/repo1,owner/repo2"
```

### 3. Generate a Combination Recipe
The most powerful feature: generate a complete architectural plan to wire multiple repositories together.

```bash
# Find repos and pipe them directly into the recipe builder
python scripts/repo_finder.py --task "video processing with OCR" --json | python scripts/recipe_builder.py --task "video processing with OCR"
```

### 4. ⚡ Vibe Mode (AI-Agent Optimized)
For ultra-fast "Vibe Coding," use the `--vibe` flag. This generates code-first, copy-paste ready blueprints specifically optimized for AI agents.

```bash
# Generate a copy-paste ready vibe recipe
python scripts/repo_finder.py --task "real-time analytics" --json | python scripts/recipe_builder.py --task "real-time analytics" --vibe
```

---

## 🛠 Features & Evolution

This version introduces several major advancements over the original repo finder:

### 📊 Advanced Scoring Engine
We no longer just look at stars. Every repo is evaluated across five dimensions:
*   **Popularity (25%)**: Stars and forks (log-scaled).
*   **Maintenance (30%)**: Recency of updates and commit frequency.
*   **Community (20%)**: Number of contributors and issue velocity.
*   **Documentation (15%)**: Quality of README and presence of examples.
*   **License (10%)**: Preference for permissive licenses (MIT, Apache, BSD).

### 🏗 Automated Recipe Builder
The `recipe_builder.py` script creates a "Combination Recipe" which includes:
*   **Architecture Patterns**: Automatically detects if you need Microservices, API Composition, or Library integration.
*   **Glue Code Estimates**: Tells you exactly how much code you'll need to write (typically 300-750 lines).
*   **Integration Steps**: A step-by-step 8-stage guide from setup to deployment.
*   **File Structure**: A recommended directory layout for your new project.

### ⚡ Vibe Mode: Code-First Composition
The new **Vibe Mode** (`--vibe`) is the ultimate toolkit for AI agents:
*   **One-Line Vibe Checks**: Instant emoji-based readiness assessment (e.g., ✅ Drop-in, 🐳 Docker-ready).
*   **Copy-Paste Infrastructure**: Generates a full `docker-compose.yml` for all services.
*   **Main Orchestration Skeleton**: Creates a `main.py` with pre-configured adapters and TODO markers.
*   **Environment Templates**: Auto-generates a `.env` file with all required API key placeholders.

---

## 📋 Comparison: Original vs. Next Version

| Feature | Original "Github Repo Finder" | New "Github-Repo-Skill" |
| :--- | :--- | :--- |
| **Primary Goal** | Finding a single useful repo. | **Building a full system** by combining repos. |
| **Search Intelligence** | Keyword-based. | **Task-to-Capability mapping.** |
| **Scoring** | Star count. | **Multi-dimensional health scoring.** |
| **Output** | List of links. | **Architectural blueprints (Recipes).** |
| **Vibe Coding** | No. | **Yes (`--vibe` flag).** |
| **Comparison** | Manual. | **Automated side-by-side analysis.** |
| **Bug Status** | Unknown. | **Fully Debugged & API Verified.** |

---

## 🔧 Installation & Setup

1. **Clone the repo:**
   ```bash
   git clone https://github.com/Ehsas317/github-repo-skill.git
   cd github-repo-skill
   ```

2. **(Optional) Set GitHub Token:**
   To avoid rate limits, set your GitHub Personal Access Token:
   ```bash
   export GITHUB_TOKEN=your_token_here
   ```

3. **Run:**
   The scripts use the Python Standard Library, so no extra `pip install` is required!

---
