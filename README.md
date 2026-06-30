# GitHub Repo Skill Debugging Guide for AI Agents

This document provides a comprehensive guide for an AI agent to understand, test, and debug the `github-repo-skill`. It includes the original skill documentation, the full source code of its components, and specific instructions for debugging.

---

## 1. Original `SKILL.md` Documentation

Below is the original `SKILL.md` file that describes the intended functionality and usage of the `github-repo-skill`.

```markdown
---
name: github-repo-skill
description: >
  Intelligent GitHub repository discovery, evaluation, and combination recipe generation.
  Use when the user wants to find existing open-source repos to solve a problem, evaluate
  repo quality, compare repositories, or generate a combination recipe for integrating
  multiple repos into a working project. Triggers on phrases like: "find repos for",
  "github repo for", "what repo should I use", "combine repos", "repo finder",
  "search github for", "evaluate repo", "compare repositories", or any task where
  the user needs to discover, assess, or integrate GitHub repositories. Core philosophy:
  "Don't build from scratch — combine battle-tested repos with minimal glue code."
  This skill is optimized for vibe coders and AI agents who want token-efficient
  solutions by composing existing work rather than reinventing it.
---

# GitHub Repo Skill

**Philosophy:** Almost everything you want to build already exists on GitHub. Your job is not to write code from scratch — it's to find the best repos and combine them with minimal glue code. This skill turns repository discovery into a systematic, repeatable process.

## When to Use This Skill

- User describes a project and needs to find repos that handle parts of it
- User wants to compare multiple repos for a specific use case
- User wants to know "what's the best repo for X?"
- User is building something and you (the agent) need to find components
- User asks about integrating multiple open-source tools
- Any vibe coding session where the fastest path is composition, not creation

## Workflow

### 1. Understand the Task

Break the user's request into **capabilities** — what does the final thing need to do? Examples:

| User Says | Capabilities |
|-----------|-------------|
| "Real-time chat with AI moderation" | WebSocket messaging + AI text classification + auth + UI |
| "E-commerce site" | Product catalog + cart + payment + auth + admin dashboard |
| "PDF processing pipeline" | PDF parsing + OCR + text extraction + export to structured formats |
| "Data sync service" | Change detection + conflict resolution + API + queue/scheduler |

### 2. Search for Repos

Use the repo finder script to discover candidates:

```bash
# Basic search for a task
python scripts/repo_finder.py --task "websocket chat server" --language javascript --max-results 10

# Search with minimum quality threshold
python scripts/repo_finder.py --task "authentication library" --language python --min-stars 500

# Get detailed metrics (slower, more accurate scoring)
python scripts/repo_finder.py --task "payment processing" --details --max-results 5
```

The script auto-generates multiple search queries from the task description, searches GitHub's API, and scores each repo on a 0-100 scale across five dimensions:

| Dimension | Weight | What It Measures |
|-----------|--------|------------------|
| Popularity | 25% | Stars, forks (log-scaled, favors steady growth) |
| Maintenance | 30% | Recency of pushes, commit frequency |
| Community | 20% | Contributors, issue velocity |
| Documentation | 15% | README quality, description, wiki, examples |
| License | 10% | Permissive license (MIT, Apache, BSD = full points) |

**Output:** JSON array of ranked repos with scores and breakdowns.

### 3. Generate Combination Recipe

Once you have repos, generate a recipe showing how to combine them:

```bash
# Pipe finder output to recipe builder
python scripts/repo_finder.py --task "chat app with AI" --json | \
  python scripts/recipe_builder.py --task "chat app with AI"

# Or from saved results
python scripts/recipe_builder.py --repos-file results.json --task "chat app with AI"
```

The recipe includes:
- **Selected repos** with assigned roles (frontend, backend, real-time, auth, AI, etc.)
- **Architecture pattern** detected from repo characteristics
- **Integration steps** (8-step process from setup to shipping)
- **Glue code estimate** (typically 300-750 lines)
- **File structure** recommendation
- **Deployment options** (Docker Compose, Vercel, AWS, etc.)
- **Risk mitigation** strategies
- **Token efficiency notes** for AI agents

### 4. Compare Specific Repos

When the user has candidates and wants a data-driven comparison:

```bash
python scripts/repo_finder.py --mode compare --repos "socketio/socket.io,ws-library/ws,oven-sh/bun"
```

Returns side-by-side scoring with the same 5-dimension breakdown.

## Scoring Interpretation Guide

| Score | Meaning | Action |
|-------|---------|--------|
| 80-100 | Exceptional | Strongly consider, likely category leader |
| 65-79 | Good | Solid choice, check specific fit for your use case |
| 50-64 | Adequate | Viable but investigate limitations carefully |
| 35-49 | Caution | Use only if no better alternatives, plan for maintenance |
| < 35 | Avoid | Not recommended for production use |

## Key Principles for Repo Combination

1. **One repo per capability.** Don't use a monolith that does everything — pick the best tool for each job.
2. **Adapter pattern.** Write thin adapters (50-200 lines each) between repos, don't modify repo internals.
3. **Docker Compose is your friend.** Containerize each service, let Docker handle the wiring.
4. **Prefer APIs over imports.** If a repo exposes an HTTP/WebSocket API, call it. Don't embed its code.
5. **Fork as insurance.** Fork repos you depend on to protect against deletion or breaking changes.
6. **Pin versions.** Never use `latest` — pin to specific tags/commits in your lock files.

## Integration Patterns

### Pattern A: API Composition (Recommended)
Each repo runs as a separate service. Your glue code is HTTP/WebSocket clients.

```
┌─────────────┐     HTTP      ┌─────────────┐     HTTP      ┌─────────────┐
│  Frontend   │◄─────────────►│   API GW    │◄─────────────►│   Auth      │
│   (Repo A)  │               │  (Your code)│               │   (Repo B)  │
└─────────────┘               └──────┬──────┘               └─────────────┘
                                     │
                                     │ HTTP
                                     ▼
                               ┌─────────────┐
                               │   Core      │
                               │  Business   │
                               │   (Repo C)  │
                               └─────────────┘
```

### Pattern B: Library Composition
Repos are installed as packages. Your glue code is import statements and function calls.

```python
# adapters/chat.py
from socketio import AsyncServer  # Repo A: websocket handling
from auth_lib import validate_jwt  # Repo B: authentication
from ai_service import moderate   # Repo C: AI moderation

async def handle_message(user_token: str, message: str):
    user = validate_jwt(user_token)      # Repo B
    if await moderate(message):           # Repo C
        await sio.emit("msg", message)    # Repo A
```

### Pattern C: Git Submodule + Build
Fork repos, modify minimally, build together.

```bash
# Your project
git submodule add https://github.com/you/fork-of-repo-A.git repos/repo-a
git submodule add https://github.com/you/fork-of-repo-B.git repos/repo-b
# Write thin orchestration layer that imports from submodules
```

## Token Efficiency for AI Agents

This skill is designed to minimize token usage when building projects:

- **300-750 lines of glue code** replaces 10,000+ lines of implementation
- **Import from repos** instead of copying their source into context
- **Adapter interfaces only** — load type definitions, not implementations
- **Point users to repo docs** for component details; your docs cover integration only
- **Docker Compose files** are self-documenting infrastructure

## Environment Setup

The scripts require Python 3.7+ and work without any external dependencies (stdlib only).

**Optional but recommended:**
```bash
# Set GitHub token for higher rate limits (5000 req/hour vs 60 req/hour)
export GITHUB_TOKEN=ghp_your_token_here
# Or
export GH_TOKEN=ghp_your_token_here
```

Generate a token at: https://github.com/settings/tokens (no scopes needed for public repo search)

## Script Reference

| Script | Purpose | Key Flags |
|--------|---------|-----------|
| `scripts/repo_finder.py` | Search, score, and rank repos | `--task`, `--language`, `--min-stars`, `--max-results`, `--details`, `--json` |
| `scripts/recipe_builder.py` | Generate combination recipes | `--task`, `--repos-file`, `--json` |

### repo_finder.py Modes
- `--mode search` (default): Find and rank repos
- `--mode recipe`: Find repos + print combination recipe
- `--mode compare`: Compare specific repos via `--repos`

### recipe_builder.py Input
- Pipe JSON from repo_finder.py: `repo_finder.py --json | recipe_builder.py --task "X"`
- From file: `--repos-file results.json`
- From comma-separated list: `--repos "owner/a,owner/b"`
```

---

## 2. Source Code: `repo_finder.py`

This is the Python script responsible for searching, scoring, and ranking GitHub repositories. It also contains a built-in, simpler recipe generation mode (`--mode recipe`) and the comparison logic.

```python
#!/usr/bin/env python3
"""
GitHub Repo Finder - Intelligent repository discovery and scoring engine.

Usage:
    python repo_finder.py --task "real-time chat app with AI moderation" [--language javascript] [--max-results 10]
    python repo_finder.py --query "websocket chat server" --language python --min-stars 100
    python repo_finder.py --task "e-commerce payment processing" --mode recipe

Modes:
    search   - Find and score individual repos (default)
    recipe   - Find repos and generate combination recipe
    compare  - Compare specific repos: --repos "owner/repo1,owner/repo2"

Environment:
    GITHUB_TOKEN - Personal access token (optional, increases rate limit)
"""

import argparse
import json
import os
import re
import sys
import urllib.request
import urllib.parse
from datetime import datetime, timezone
from typing import Dict, List, Optional


GITHUB_API = "https://api.github.com"


def get_auth_headers() -> dict:
    """Build request headers with optional auth."""
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "github-repo-skill/1.0"
    }
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def github_api_get(endpoint: str, params: dict = None) -> dict:
    """Make authenticated GET request to GitHub API."""
    url = f"{GITHUB_API}{endpoint}"
    if params:
        query = urllib.parse.urlencode(params)
        url = f"{url}?{query}"

    req = urllib.request.Request(url, headers=get_auth_headers())
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        if e.code == 403:
            print("[!] Rate limited. Set GITHUB_TOKEN env var for higher limits.", file=sys.stderr)
        elif e.code == 422:
            body = e.read().decode()
            print(f"[!] Invalid query: {body}", file=sys.stderr)
        else:
            print(f"[!] API error {e.code}: {e.reason}", file=sys.stderr)
        return {}
    except Exception as e:
        print(f"[!] Request failed: {e}", file=sys.stderr)
        return {}


def parse_date(date_str: str) -> Optional[datetime]:
    """Parse ISO date string to datetime."""
    if not date_str:
        return None
    try:
        return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
    except:
        return None


def days_since(date_str: str) -> int:
    """Calculate days since a date string."""
    dt = parse_date(date_str)
    if not dt:
        return 9999
    return (datetime.now(timezone.utc) - dt).days


def search_repos(query: str, language: Optional[str] = None, min_stars: int = 10,
                 sort: str = "best-match", order: str = "desc", per_page: int = 30) -> List[dict]:
    """Search GitHub repositories with query."""
    q = query
    if language:
        q = f"{q} language:{language}"
    if min_stars > 0:
        q = f"{q} stars:>={min_stars}"

    params = {
        "q": q,
        "sort": sort,
        "order": order,
        "per_page": min(per_page, 100)
    }
    data = github_api_get("/search/repositories", params)
    return data.get("items", [])


def get_repo_details(owner: str, repo: str) -> dict:
    """Fetch detailed repo info including community metrics."""
    details = github_api_get(f"/repos/{owner}/{repo}")
    if not details:
        return {}

    # Get additional metrics
    commits = github_api_get(f"/repos/{owner}/{repo}/commits", {"per_page": 1})
    contributors = github_api_get(f"/repos/{owner}/{repo}/contributors", {"per_page": 1})

    # Get last 100 commits for activity analysis
    recent_commits = github_api_get(
        f"/repos/{owner}/{repo}/commits",
        {"per_page": 100}
    ) or []

    details["_recent_commit_count"] = len(recent_commits)
    details["_contributor_count"] = len(contributors) if isinstance(contributors, list) else 0

    return details


def score_repo(repo: dict, details: dict = None) -> dict:
    """
    Calculate a composite quality score (0-100) for a repository.

    Factors:
        - popularity (stars, forks): 25%
        - maintenance (recency, commit frequency): 30%
        - community (contributors, issues/PRs): 20%
        - documentation (has README, has wiki, description quality): 15%
        - license (exists, permissive): 10%
    """
    score = {
        "total": 0,
        "popularity": 0,
        "maintenance": 0,
        "community": 0,
        "documentation": 0,
        "license": 0,
        "details": {}
    }

    stars = repo.get("stargazers_count", 0)
    forks = repo.get("forks_count", 0)
    updated = repo.get("updated_at", "")
    pushed = repo.get("pushed_at", "")
    open_issues = repo.get("open_issues_count", 0)
    has_wiki = repo.get("has_wiki", False)
    has_pages = repo.get("has_pages", False)
    description = repo.get("description") or ""
    license_info = repo.get("license")

    # Popularity score (0-25): log scale for stars
    if stars > 0:
        star_score = min(25, (stars / 1000) ** 0.5 * 5 + min(stars / 100, 10))
    else:
        star_score = 0
    fork_score = min(5, forks / 50)
    score["popularity"] = min(25, star_score + fork_score)

    # Maintenance score (0-30): recency + commit activity
    days_since_push = days_since(pushed)
    days_since_update = days_since(updated)

    if days_since_push <= 7:
        recency_score = 20
    elif days_since_push <= 30:
        recency_score = 18
    elif days_since_push <= 90:
        recency_score = 14
    elif days_since_push <= 180:
        recency_score = 10
    elif days_since_push <= 365:
        recency_score = 6
    else:
        recency_score = 2

    # Commit frequency score
    recent_commits = details.get("_recent_commit_count", 0) if details else 0
    commit_score = min(10, recent_commits / 10)
    score["maintenance"] = recency_score + commit_score

    # Community score (0-20): contributors, issue activity
    contributors = details.get("_contributor_count", 0) if details else 0
    contrib_score = min(10, contributors / 5)
    issue_score = min(10, open_issues / 10) if open_issues < 500 else 5  # Too many issues can be bad
    score["community"] = contrib_score + issue_score

    # Documentation score (0-15): README, description, wiki
    desc_score = min(5, len(description) / 50) if description else 0
    wiki_score = 3 if has_wiki else 0
    pages_score = 2 if has_pages else 0
    readme_score = 5  # Assume README exists (GitHub shows repo)
    score["documentation"] = min(15, desc_score + wiki_score + pages_score + readme_score)

    # License score (0-10)
    if license_info:
        spdx = license_info.get("spdx_id", "")
        permissive_licenses = {"MIT", "Apache-2.0", "BSD-3-Clause", "BSD-2-Clause", "ISC", "Unlicense"}
        if spdx in permissive_licenses:
            score["license"] = 10
        elif spdx:
            score["license"] = 7
        else:
            score["license"] = 5
    else:
        score["license"] = 0

    score["total"] = (
        score["popularity"] +
        score["maintenance"] +
        score["community"] +
        score["documentation"] +
        score["license"]
    )

    score["details"] = {
        "stars": stars,
        "forks": forks,
        "days_since_push": days_since_push,
        "days_since_update": days_since_update,
        "open_issues": open_issues,
        "contributors": contributors,
        "recent_commits": recent_commits,
        "language": repo.get("language"),
        "license": license_info.get("spdx_id") if license_info else None,
        "description": description[:200] if description else "",
    }

    return score


def extract_topics(task: str) -> List[str]:
    """Extract likely technology topics from a task description."""
    # Common technology keywords mapped to search terms
    tech_map = {
        # Languages
        "python": "python", "javascript": "javascript", "typescript": "typescript",
        "rust": "rust", "go": "go", "golang": "go", "java": "java",
        "ruby": "ruby", "kotlin": "kotlin", "swift": "swift", "cpp": "c++",
        "c++": "c++", "csharp": "c#", "c#": "c#", "php": "php",
        # Frontend
        "react": "react", "vue": "vue", "angular": "angular", "svelte": "svelte",
        "nextjs": "nextjs", "nuxt": "nuxt", "frontend": "frontend",
        # Backend
        "node": "nodejs", "nodejs": "nodejs", "express": "express",
        "fastapi": "fastapi", "django": "django", "flask": "flask",
        "spring": "spring-boot", "laravel": "laravel",
        # Database
        "database": "database", "sql": "sql", "postgres": "postgresql",
        "mongodb": "mongodb", "redis": "redis", "sqlite": "sqlite",
        "prisma": "prisma", "orm": "orm",
        # Real-time
        "websocket": "websocket", "real-time": "realtime", "realtime": "realtime",
        "chat": "chat", "messaging": "messaging", "socket": "socket.io",
        # AI/ML
        "ai": "artificial-intelligence", "machine learning": "machine-learning",
        "ml": "machine-learning", "llm": "llm", "gpt": "gpt",
        "neural": "neural-network", "tensorflow": "tensorflow", "pytorch": "pytorch",
        # DevOps
        "docker": "docker", "kubernetes": "kubernetes", "k8s": "kubernetes",
        "ci/cd": "cicd", "github actions": "github-actions", "aws": "aws",
        "terraform": "terraform", "ansible": "ansible",
        # Auth
        "auth": "authentication", "authentication": "authentication",
        "oauth": "oauth", "jwt": "jwt", "sso": "sso",
        # Other
        "payment": "payment", "stripe": "stripe", "billing": "billing",
        "search": "search", "elasticsearch": "elasticsearch",
        "queue": "queue", "kafka": "kafka", "rabbitmq": "rabbitmq",
        "monitoring": "monitoring", "logging": "logging",
        "testing": "testing", "e2e": "e2e-testing",
        "graphql": "graphql", "rest": "rest-api", "api": "api",
        "scraping": "web-scraping", "crawler": "web-scraper",
        "blockchain": "blockchain", "crypto": "cryptocurrency",
        "image": "image-processing", "video": "video-processing",
        "pdf": "pdf", "csv": "csv", "excel": "excel",
    }

    task_lower = task.lower()
    found = []
    for keyword, search_term in tech_map.items():
        if keyword in task_lower and search_term not in found:
            found.append(search_term)
    return found


def generate_search_queries(task: str, language: Optional[str] = None) -> List[str]:
    """Generate multiple search queries from a task description."""
    queries = []
    topics = extract_topics(task)

    # Primary query: full task
    queries.append(task)

    # If we detected specific technologies, add targeted queries
    if language:
        queries.append(f"{task} language:{language}")

    # Add topic-based queries
    for topic in topics[:3]:
        q = topic.replace("-", " ")
        if language:
            q = f"{q} language:{language}"
        if q not in queries:
            queries.append(q)

    # Add capability-based breakdowns
    words = task.lower().split()
    if any(w in words for w in ["chat", "messaging", "real-time", "realtime", "websocket"]):
        queries.append(f"websocket chat server {"language:" + language if language else ""}".strip())
    if any(w in words for w in ["auth", "login", "authentication", "oauth", "jwt"]):
        queries.append(f"authentication jwt oauth {"language:" + language if language else ""}".strip())
    if any(w in words for w in ["payment", "stripe", "billing", "subscription"]):
        queries.append(f"payment processing stripe {"language:" + language if language else ""}".strip())
    if any(w in words for w in ["ai", "ml", "machine", "learning", "llm", "gpt"]):
        queries.append(f"llm ai integration {"language:" + language if language else ""}".strip())

    # Deduplicate
    seen = set()
    unique = []
    for q in queries:
        key = q.lower().strip()
        if key not in seen:
            seen.add(key)
            unique.append(q)
    return unique[:5]


def find_repos(task: str, language: Optional[str] = None, min_stars: int = 50,
               max_results: int = 10, fetch_details: bool = False) -> List[dict]:
    """
    Main entry point: find and score repos for a task.
    Returns ranked list of repos with scores.
    """
    queries = generate_search_queries(task, language)
    all_repos = []
    seen_full_names = set()

    for query in queries:
        repos = search_repos(query, language=language, min_stars=min_stars,
                           sort="stars", order="desc", per_page=30)
        for repo in repos:
            fn = repo.get("full_name")
            if fn and fn not in seen_full_names:
                seen_full_names.add(fn)
                all_repos.append(repo)

    # Score each repo
    results = []
    for repo in all_repos:
        details = None
        if fetch_details:
            owner, name = repo["full_name"].split("/", 1)
            details = get_repo_details(owner, name)

        score = score_repo(repo, details)
        results.append({
            "full_name": repo["full_name"],
            "html_url": repo["html_url"],
            "description": repo.get("description", ""),
            "language": repo.get("language"),
            "stars": repo.get("stargazers_count", 0),
            "forks": repo.get("forks_count", 0),
            "updated_at": repo.get("updated_at"),
            "pushed_at": repo.get("pushed_at"),
            "open_issues": repo.get("open_issues_count", 0),
            "license": repo.get("license", {}).get("spdx_id") if repo.get("license") else None,
            "topics": repo.get("topics", []),
            "score": score["total"],
            "score_breakdown": {
                "popularity": score["popularity"],
                "maintenance": score["maintenance"],
                "community": score["community"],
                "documentation": score["documentation"],
                "license": score["license"]
            },
            "details": score["details"]
        })

    # Sort by score descending
    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:max_results]


def generate_recipe(repos: List[dict], task: str) -> dict:
    """Generate a combination recipe from selected repos."""
    recipe = {
        "task": task,
        "philosophy": "Combine existing repos instead of building from scratch",
        "selected_repos": [],
        "integration_strategy": "",
        "setup_steps": [],
        "token_efficiency_notes": []
    }

    # Select top repos covering different capabilities
    selected = repos[:5]
    for i, repo in enumerate(selected, 1):
        recipe["selected_repos"].append({
            "rank": i,
            "name": repo["full_name"],
            "url": repo["html_url"],
            "description": repo["description"],
            "language": repo["language"],
            "stars": repo["stars"],
            "score": repo["score"],
            "role": f"Component {i}: {repo["description"][:80] if repo["description"] else "No description"}"
        })

    # Generate integration strategy
    langs = [r["language"] for r in selected if r["language"]]
    primary_lang = max(set(langs), key=langs.count) if langs else "your language"

    recipe["integration_strategy"] = (
        f"1. Clone/fork the selected repositories\n"
        f"2. Identify the API boundaries and data contracts\n"
        f"3. Create a thin orchestration layer in {primary_lang or "your preferred language"}\n"
        f"4. Wire repos together using their native APIs (HTTP, WebSocket, gRPC, or function calls)\n"
        f"5. Add configuration management and environment variables\n"
        f"6. Write minimal glue code (typically <200 lines)"
    )

    recipe["setup_steps"] = [
        "Review each repo's README for setup instructions",
        "Check for Docker/docker-compose files for quick starts",
        "Identify environment variables and configuration options",
        "Look for example/ or demo/ directories",
        "Check if repos have SDK/client libraries available",
        "Fork repos you need to modify; use package managers for others"
    ]

    recipe["token_efficiency_notes"] = [
        f"Instead of writing full implementations, import from: {[r["full_name"] for r in selected[:3]]}",
        "Use each repo's CLI/API rather than embedding logic",
        "Look for composable architectures (microservices, plugins, middleware)",
        "Prefer repos with good TypeScript definitions or OpenAPI specs",
        "Combine via Docker Compose for infrastructure isolation"
    ]

    return recipe


def compare_repos(repo_specs: List[str]) -> List[dict]:
    """Compare specific repositories side by side."""
    results = []
    for spec in repo_specs:
        if "/" not in spec:
            continue
        owner, repo = spec.split("/", 1)
        data = github_api_get(f"/repos/{owner}/{repo}")
        if data:
            details = get_repo_details(owner, repo)
            score = score_repo(data, details)
            results.append({
                "full_name": data["full_name"],
                "html_url": data["html_url"],
                "description": data.get("description", ""),
                "language": data.get("language"),
                "stars": data.get("stargazers_count", 0),
                "forks": data.get("forks_count", 0),
                "score": score["total"],
                "score_breakdown": score
            })

    results.sort(key=lambda x: x["score"], reverse=True)
    return results


def print_results(results: List[dict], mode: str = "search"):
    """Pretty print results to stdout."""
    if not results:
        print("No repositories found.")
        return

    if mode == "compare":
        print(f"\n{'='*80}")
        print(f"  REPO COMPARISON")
        print(f"{'='*80}")
    else:
        print(f"\n{'='*80}")
        print(f"  FOUND {len(results)} REPOSITORIES")
        print(f"{'='*80}")

    for i, repo in enumerate(results, 1):
        bd = repo.get("score_breakdown", {})
        breakdown = ""
        if isinstance(bd, dict) and "popularity" in bd:
            breakdown = (f"  [pop:{bd['popularity']:.0f} maint:{bd['maintenance']:.0f} "
                        f"comm:{bd['community']:.0f} docs:{bd['documentation']:.0f} lic:{bd['license']:.0f}]")

        print(f"\n  #{i} {repo['full_name']} - Score: {repo['score']:.1f}/100")
        print(f"  {'─'*76}")
        print(f"  URL: {repo['html_url']}")
        print(f"  Stars: {repo['stars']:,} | Forks: {repo['forks']:,} | "
              f"Issues: {repo.get('open_issues', 'N/A')} | Lang: {repo.get('language', 'N/A')}")
        print(f"  License: {repo.get('license', 'N/A')}")
        if breakdown:
            print(f"  {breakdown}")
        desc = repo.get('description', '')
        if desc:
            print(f"  Description: {desc[:120]}")


def print_recipe(recipe: dict):
    """Print combination recipe."""
    print(f"\n{'='*80}")
    print(f"  COMBINATION RECIPE: {recipe['task']}")
    print(f"{'='*80}")
    print(f"\n  Philosophy: {recipe['philosophy']}")

    print(f"\n  SELECTED REPOSITORIES:")
    print(f"  {'─'*76}")
    for repo in recipe["selected_repos"]:
        print(f"  {repo['rank']}. {repo['name']} (Score: {repo['score']:.1f}, Stars: {repo['stars']:,})")
        print(f"     Role: {repo['role']}")
        print(f"     URL: {repo['url']}")
        print()

    print(f"  INTEGRATION STRATEGY:")
    print(f"  {'─'*76}")
    for line in recipe["integration_strategy"].split("\n"):
        print(f"  {line}")

    print(f"\n  SETUP STEPS:")
    print(f"  {'─'*76}")
    for step in recipe["setup_steps"]:
        print(f"  - {step}")

    print(f"\n  TOKEN EFFICIENCY NOTES:")
    print(f"  {'─'*76}")
    for note in recipe["token_efficiency_notes"]:
        print(f"  - {note}")

    print(f"\n{'='*80}")


def main():
    parser = argparse.ArgumentParser(description="GitHub Repo Finder - Find the perfect repos for your task")
    parser.add_argument("--task", type=str, help="Task description (e.g., 'real-time chat with AI moderation')")
    parser.add_argument("--query", type=str, help="Direct search query")
    parser.add_argument("--language", type=str, help="Filter by programming language")
    parser.add_argument("--min-stars", type=int, default=50, help="Minimum stars (default: 50)")
    parser.add_argument("--max-results", type=int, default=10, help="Max results (default: 10)")
    parser.add_argument("--mode", choices=["search", "recipe", "compare"], default="search",
                       help="Output mode (default: search)")
    parser.add_argument("--repos", type=str, help="Repos to compare (comma-separated: 'owner/repo1,owner/repo2')")
    parser.add_argument("--details", action="store_true", help="Fetch detailed metrics (slower)")
    parser.add_argument("--json", action="store_true", help="Output as JSON")

    args = parser.parse_args()

    if args.mode == "compare" and args.repos:
        repo_specs = [r.strip() for r in args.repos.split(",")]
        results = compare_repos(repo_specs)
        if args.json:
            print(json.dumps(results, indent=2))
        else:
            print_results(results, mode="compare")
        return

    if not args.task and not args.query:
        parser.print_help()
        sys.exit(1)

    query = args.query or args.task
    results = find_repos(
        task=query,
        language=args.language,
        min_stars=args.min_stars,
        max_results=args.max_results,
        fetch_details=args.details
    )

    if args.mode == "recipe":
        recipe = generate_recipe(results, args.task or args.query)
        if args.json:
            print(json.dumps(recipe, indent=2))
        else:
            print_results(results)
            print_recipe(recipe)
    else:
        if args.json:
            print(json.dumps(results, indent=2))
        else:
            print_results(results)


if __name__ == "__main__":
    main()
```

---

## 3. Source Code: `recipe_builder.py`

This script is designed to take the JSON output from `repo_finder.py` and generate a more detailed combination recipe. It offers richer architectural insights and integration guidance.

```python
#!/usr/bin/env python3
"""
Recipe Builder - Generate combination recipes from discovered repositories.

Reads repo_finder.py JSON output and creates actionable integration guides.

Usage:
    python repo_finder.py --task "chat app" --json | python recipe_builder.py --task "chat app"
    python recipe_builder.py --repos-file repos.json --task "e-commerce platform"
    python recipe_builder.py --repos "socketio/socket.io,auth0/node-jsonwebtoken,stripe/stripe-node"
"""

import argparse
import json
import sys
from typing import List, Dict


def detect_architecture_pattern(repos: List[dict]) -> str:
    """Determine the best architecture pattern based on repo characteristics."""
    languages = [r.get("language") for r in repos if r.get("language")]
    topics = []
    for r in repos:
        topics.extend(r.get("topics", []))
    topics = [t.lower() for t in topics]

    # Check for specific patterns
    has_websocket = any(t in topics for t in ["websocket", "realtime", "socket", "sse"])
    has_api = any(t in topics for t in ["api", "rest", "graphql", "http"])
    has_frontend = any(t in topics for t in ["react", "vue", "angular", "svelte", "ui", "component", "frontend"])
    has_backend = any(t in topics for t in ["backend", "server", "api", "rest", "framework", "microservice"])
    has_ml = any(t in topics for t in ["machine-learning", "ai", "llm", "gpt", "neural"])
    has_docker = any(t in topics for t in ["docker", "container", "kubernetes"])

    patterns = []

    if has_frontend and has_backend:
        patterns.append("Full-Stack: Frontend + Backend API + (optional) Database")
    if has_websocket:
        patterns.append("Real-Time: WebSocket/SSE for live updates")
    if has_ml:
        patterns.append("AI-Powered: LLM/ML service integrated via API")
    if has_docker:
        patterns.append("Containerized: Docker Compose for orchestration")
    if len(languages) > 1:
        patterns.append(f"Polyglot: {', '.join(set(languages[:3]))} services")

    if not patterns:
        patterns.append("Modular: Import libraries and wire with thin orchestration")

    return "\n  ".join(patterns)


def generate_glue_code_estimate(repos: List[dict]) -> Dict:
    """Estimate the glue code needed to combine repos."""
    estimates = {
        "config_code": "50-100 lines (environment variables, service URLs)",
        "api_adapters": "100-200 lines per external service (HTTP clients, type mappings)",
        "data_transforms": "50-150 lines (converting between repo data formats)",
        "orchestration": "100-300 lines (service startup, health checks, routing)",
        "total_estimate": "300-750 lines of glue code"
    }

    # Adjust based on repo types
    languages = [r.get("language") for r in repos if r.get("language")]
    if "TypeScript" in languages or "JavaScript" in languages:
        estimates["api_adapters"] = "80-150 lines per service (strong typing helps)"
    if "Python" in languages:
        estimates["api_adapters"] = "60-120 lines per service (dynamic, fast prototyping)"

    return estimates


def generate_combination_recipe(repos: List[dict], task: str) -> dict:
    """Generate a complete combination recipe."""
    recipe = {
        "task": task,
        "philosophy": "Don't build from scratch. Combine battle-tested repos with minimal glue code.",
        "repos": [],
        "architecture": detect_architecture_pattern(repos),
        "integration_steps": [],
        "glue_code_estimate": generate_glue_code_estimate(repos),
        "file_structure": {},
        "dependency_strategy": "",
        "deployment_options": [],
        "risk_mitigation": [],
        "ai_agent_notes": []
    }

    # Map repos to roles
    for i, repo in enumerate(repos[:5], 1):
        role = detect_role(repo)
        recipe["repos"].append({
            "rank": i,
            "name": repo["full_name"],
            "url": repo["html_url"],
            "role": role,
            "language": repo.get("language"),
            "integration_method": suggest_integration_method(repo),
            "setup_complexity": estimate_setup_complexity(repo),
            "key_files": suggest_key_files(repo)
        })

    # Integration steps
    recipe["integration_steps"] = [
        "1. SETUP: Clone each repo and get it running independently",
        "2. BOUNDARIES: Identify the 'surface area' - what APIs/exports each repo provides",
        "3. CONTRACTS: Define data shapes that flow between repos (shared types/interfaces)",
        "4. ADAPTERS: Write thin adapter functions to convert between repo formats",
        "5. ORCHESTRATE: Create a main entry point that initializes all services",
        "6. CONFIG: Extract all configuration to environment variables",
        "7. TEST: Verify each integration point independently",
        "8. SHIP: Docker Compose or deploy to hosting"
    ]

    # File structure
    recipe["file_structure"] = {
        "docker-compose.yml": "Orchestrates all services",
        ".env": "All configuration (API keys, ports, URLs)",
        "src/": {
            "index.ts/py/js": "Main orchestration entry point",
            "config/": "Configuration loading and validation",
            "adapters/": "One file per external repo integration",
            "types/": "Shared TypeScript types / Python dataclasses",
            "utils/": "Helpers for HTTP, auth, logging"
        },
        "repos/": "Git submodules or cloned repos (if modifying)"
    }

    # Dependency strategy
    primary = repos[0].get("language") if repos else "your language"
    recipe["dependency_strategy"] = (
        f"Primary language: {primary}\n"
        f"- Use package manager (npm/pip/cargo/go mod) for installable libraries\n"
        f"- Use Git submodules for repos you need to modify\n"
        f"- Use Docker images for infrastructure services (DBs, caches)\n"
        f"- Use language-native FFI/binding for cross-language integration"
    )

    # Deployment
    recipe["deployment_options"] = [
        "Docker Compose: Easiest local + production parity",
        "Vercel/Railway/Render: For full-stack with frontend",
        "AWS/GCP: For services needing specific infrastructure",
        "Self-hosted: For data-sensitive or high-performance needs"
    ]

    # Risk mitigation
    recipe["risk_mitigation"] = [
        "Fork critical repos (protect against deletion/changes)",
        "Pin to specific versions/tags (not 'latest')",
        "Write adapter layer (don't import deeply into repo internals)",
        "Monitor repo health monthly (stars, issues, last commit)",
        "Have swap candidates (identify backup repos for each component)"
    ]

    # AI agent notes - the key value prop
    recipe["ai_agent_notes"] = [
        "TOKEN EFFICIENCY: Import from repos rather than rewriting. Each line of glue code replaces 50-200 lines of implementation.",
        "CONTEXT WINDOW: Load only the adapter interfaces, not full repo source. Use package types/declarations.",
        "ITERATION SPEED: Modify adapters not implementations. Swap repos by changing adapter, not core logic.",
        "DEBUGGING: Issues are likely in adapters (your code) not repos (battle-tested). Narrow debugging surface.",
        "DOCUMENTATION: Point users to repo docs for component details. Your docs only cover integration."
    ]

    return recipe


def detect_role(repo: dict) -> str:
    """Auto-detect the role of a repo based on its metadata."""
    desc = (repo.get("description") or "").lower()
    topics = [t.lower() for t in repo.get("topics", [])]
    name = repo.get("full_name", "").lower()
    combined = f"{name} {desc} {' '.join(topics)}"

    role_patterns = [
        ("frontend/ui", ["react", "vue", "angular", "svelte", "ui", "component", "frontend",
                        "dashboard", "admin", "spa", "template", "portfolio", "landing"]),
        ("backend/api", ["api", "rest", "graphql", "server", "backend", "framework",
                        "microservice", "gateway", "middleware", "routing"]),
        ("real-time", ["websocket", "socket", "realtime", "sse", "event", "stream",
                      "live", "chat", "messaging", "pubsub"]),
        ("auth/security", ["auth", "jwt", "oauth", "sso", "password", "session",
                          "security", "crypt", "encrypt", "login", "identity"]),
        ("database/orm", ["database", "orm", "prisma", "sql", "mongodb", "redis",
                         "sqlite", "postgres", "elastic", "search"]),
        ("ai/ml", ["llm", "gpt", "ai", "machine learning", "neural", "tensorflow",
                   "pytorch", "transformer", "embedding", "classification"]),
        ("devops/tooling", ["docker", "kubernetes", "terraform", "ansible", "ci",
                           "deploy", "monitor", "log", "test", "lint", "build"]),
        ("payment/billing", ["payment", "stripe", "billing", "subscription", "invoice",
                            "checkout", "commerce", "e-commerce"]),
        ("storage/files", ["s3", "storage", "file", "upload", "cdn", "image",
                          "video", "media", "asset"]),
        ("communication", ["email", "sms", "notification", "push", "webhook",
                          "slack", "discord", "telegram"]),
    ]

    scores = {}
    for role, keywords in role_patterns:
        scores[role] = sum(1 for kw in keywords if kw in combined)

    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "utility/library"


def suggest_integration_method(repo: dict) -> str:
    """Suggest how to integrate this repo into your project."""
    lang = repo.get("language", "").lower()
    topics = [t.lower() for t in repo.get("topics", [])]

    if "docker" in topics or "container" in topics:
        return "Docker container - add to docker-compose.yml"
    if lang in ["javascript", "typescript"]:
        return "npm/yarn install OR git submodule + import"
    if lang == "python":
        return "pip install OR git submodule + import"
    if lang == "go":
        return "go get OR git submodule + import"
    if lang == "rust":
        return "cargo add OR git submodule + import"

    has_api = any(t in topics for t in ["api", "rest", "graphql", "http"])
    if has_api:
        return "HTTP API client - call its endpoints"

    return "Git submodule + build from source OR use as service"


def estimate_setup_complexity(repo: dict) -> str:
    """Estimate how complex it is to set up this repo."""
    stars = repo.get("stars", 0)
    topics = repo.get("topics", [])
    desc = repo.get("description", "")

    has_docker = any(t in topics for t in ["docker", "container", "compose"])
    has_docs = bool(desc) and len(desc) > 50

    if has_docker:
        return "Low: Docker setup likely one command"
    if stars > 5000 and has_docs:
        return "Low-Medium: Well documented, probably has quickstart"
    if stars > 1000:
        return "Medium: Read README carefully, check for example/ dir"
    return "Medium-High: May need manual configuration, check issues for setup help"


def suggest_key_files(repo: dict) -> List[str]:
    """Suggest key files to look at in the repo."""
    name = repo.get("full_name", "").split("/")[-1] if "/" in repo.get("full_name", "") else ""
    return [
        "README.md - Setup and API docs",
        f"package.json/pyproject.toml/Cargo.toml - Dependencies",
        f"docker-compose.yml/Dockerfile - Container setup",
        f"src/index.* or {name}/__init__.py - Entry point",
        "examples/ or demo/ - Usage examples",
        ".env.example - Configuration options"
    ]


def print_recipe(recipe: dict):
    """Pretty print a combination recipe."""
    print(f"\n{'='*80}")
    print(f"  COMBINATION RECIPE: {recipe['task']}")
    print(f"{'='*80}")
    print(f"\n  {recipe['philosophy']}")

    print(f"\n  {'─'*76}")
    print(f"  SELECTED REPOSITORIES:")
    print(f"  {'─'*76}")
    for repo in recipe["repos"]:
        print(f"\n  [{repo['rank']}] {repo['name']}")
        print(f"      Role: {repo['role']}")
        print(f"      Language: {repo['language'] or 'N/A'}")
        print(f"      Integration: {repo['integration_method']}")
        print(f"      Setup: {repo['setup_complexity']}")
        print(f"      URL: {repo['url']}")
        print(f"      Key files to check:")
        for f in repo['key_files'][:3]:
            print(f"        - {f}")

    print(f"\n  {'─'*76}")
    print(f"  ARCHITECTURE PATTERN:")
    print(f"  {'─'*76}")
    print(f"  {recipe['architecture']}")

    print(f"\n  {'─'*76}")
    print(f"  INTEGRATION STEPS:")
    print(f"  {'─'*76}")
    for step in recipe["integration_steps"]:
        print(f"  {step}")

    print(f"\n  {'─'*76}")
    print(f"  GLUE CODE ESTIMATE:")
    print(f"  {'─'*76}")
    for k, v in recipe["glue_code_estimate"].items():
        print(f"  {k}: {v}")

    print(f"\n  {'─'*76}")
    print(f"  DEPENDENCY STRATEGY:")
    print(f"  {'─'*76}")
    print(f"  {recipe['dependency_strategy']}")

    print(f"\n  {'─'*76}")
    print(f"  DEPLOYMENT OPTIONS:")
    print(f"  {'─'*76}")
    for opt in recipe["deployment_options"]:
        print(f"  - {opt}")

    print(f"\n  {'─'*76}")
    print(f"  RISK MITIGATION:")
    print(f"  {'─'*76}")
    for risk in recipe["risk_mitigation"]:
        print(f"  - {risk}")

    print(f"\n  {'─'*76}")
    print(f"  FOR AI AGENTS (TOKEN EFFICIENCY):")
    print(f"  {'─'*76}")
    for note in recipe["ai_agent_notes"]:
        print(f"  - {note}")

    print(f"\n{'='*80}")
    print(f"  NEXT STEPS:")
    print(f"  1. Review each repo's README (10 mins each)")
    print(f"  2. Write docker-compose.yml with all services")
    print(f"  3. Create adapter files in src/adapters/")
    print(f"  4. Write main orchestration in src/index.*")
    print(f"  5. Test each integration point")
    print(f"  6. Ship it")
    print(f"{'='*80}\n")


def main():
    parser = argparse.ArgumentParser(description="Build combination recipes from GitHub repos")
    parser.add_argument("--task", type=str, required=True, help="Original task description")
    parser.add_argument("--repos-file", type=str, help="JSON file from repo_finder.py")
    parser.add_argument("--repos", type=str, help="Comma-separated list of owner/repo pairs")
    parser.add_argument("--json", action="store_true", help="Output as JSON")

    args = parser.parse_args()

    repos = []

    if args.repos_file:
        with open(args.repos_file) as f:
            repos = json.load(f)
    elif args.repos:
        # Build minimal repo dicts from names
        for spec in args.repos.split(","):
            spec = spec.strip()
            if "/" in spec:
                repos.append({
                    "full_name": spec,
                    "html_url": f"https://github.com/{spec}",
                    "description": "",
                    "language": None,
                    "stars": 0,
                    "topics": []
                })
    else:
        try:
            stdin_data = sys.stdin.read()
            if stdin_data.strip():
                repos = json.loads(stdin_data)
        except (json.JSONDecodeError, EOFError):
            pass

    if not repos:
        print("Error: No repos provided. Use --repos-file, --repos, or pipe JSON from repo_finder.py",
              file=sys.stderr)
        sys.exit(1)

    recipe = generate_combination_recipe(repos, args.task)

    if args.json:
        print(json.dumps(recipe, indent=2))
    else:
        print_recipe(recipe)


if __name__ == "__main__":
    main()
```

---

## 4. Debugging Guide for AI Agents

This section highlights key aspects for an AI agent to consider when debugging or using the `github-repo-skill`.

### 4.1. Key Differences and Discrepancies

It's crucial to understand that the `SKILL.md` describes the *ideal* output and capabilities, which are primarily delivered by piping `repo_finder.py --json` output into `recipe_builder.py`. There is a simpler, built-in recipe generation mode within `repo_finder.py` itself (`--mode recipe`), but it is less comprehensive.

| Feature | `SKILL.md` Description (via `recipe_builder.py`) | `repo_finder.py --mode recipe` Implementation |
|---|---|---|
| **Role Assignment** | "Selected repos with assigned roles (frontend, backend, real-time, auth, AI, etc.)" | Assigns a generic role based on the first 80 characters of the description: `Component X: {description snippet}`. |
| **Architecture Pattern** | "Architecture pattern detected from repo characteristics" (e.g., Full-Stack, Real-Time, AI-Powered) | **Not implemented.** This specific feature is only available through `recipe_builder.py`. |
| **Integration Steps** | "8-step process from setup to shipping" | A simpler, 6-step process is provided. |
| **Glue Code Estimate** | "typically 300-750 lines" with detailed breakdown | A simpler estimate of "typically <200 lines" is given, without detailed breakdown. |
| **File Structure Recommendation** | "File structure recommendation" (e.g., `src/`, `adapters/`, `types/`) | **Not implemented.** This specific feature is only available through `recipe_builder.py`. |
| **Deployment Options** | "Deployment options" (Docker Compose, Vercel, AWS, etc.) | **Not implemented.** This specific feature is only available through `recipe_builder.py`. |
| **Risk Mitigation** | "Risk mitigation strategies" | **Not implemented.** This specific feature is only available through `recipe_builder.py`. |

**Conclusion:** For a truly comprehensive recipe, always use the pipeline: `repo_finder.py --json | recipe_builder.py`. The `--mode recipe` in `repo_finder.py` is a quick, less detailed alternative.

### 4.2. Common Debugging Scenarios and Solutions

1.  **Rate Limiting (403 Error):**
    *   **Symptom:** `[!] Rate limited. Set GITHUB_TOKEN env var for higher limits.`
    *   **Cause:** GitHub API rate limits (60 requests/hour for unauthenticated, 5000 requests/hour with token) have been exceeded.
    *   **Solution:** Ensure `GITHUB_TOKEN` or `GH_TOKEN` environment variable is set with a valid GitHub Personal Access Token. No scopes are needed for public repo search. Generate one at [https://github.com/settings/tokens](https://github.com/settings/tokens).

2.  **Invalid Query (422 Error):**
    *   **Symptom:** `[!] Invalid query: {error_details}`
    *   **Cause:** The search query passed to GitHub API is malformed or too complex.
    *   **Solution:** Simplify the `--task` or `--query` parameter. Avoid overly long or highly specific phrases. The `generate_search_queries` function tries to mitigate this by breaking down tasks, but very unusual inputs might still fail.

3.  **No Repositories Found:**
    *   **Symptom:** `No repositories found.`
    *   **Cause:** The search query was too restrictive (e.g., very high `--min-stars`) or the task description didn't yield relevant results.
    *   **Solution:** Broaden the search by reducing `--min-stars`, removing `--language` filter, or rephrasing the `--task` to be more general.

4.  **`recipe_builder.py` Error: No Repos Provided:**
    *   **Symptom:** `Error: No repos provided. Use --repos-file, --repos, or pipe JSON from repo_finder.py`
    *   **Cause:** `recipe_builder.py` did not receive any input repositories, either from a file, a comma-separated list, or stdin.
    *   **Solution:** Ensure `repo_finder.py --json` output is correctly piped, or provide a valid `--repos-file` or `--repos` argument.

5.  **Inaccurate Scoring/Ranking:**
    *   **Symptom:** Repositories that seem highly relevant are ranked lower than expected.
    *   **Cause:** The scoring algorithm's weights might not perfectly align with the specific project's priorities, or the GitHub metadata (description, topics) for a particular repo might be incomplete.
    *   **Solution:** Understand the scoring dimensions (Popularity, Maintenance, Community, Documentation, License) and their weights. If a specific dimension is more critical for the current task, manually adjust the selection based on the `score_breakdown` or use the `--details` flag for more granular information.

### 4.3. How to Test Each Mode (for AI Agents)

To ensure the skill is functioning correctly, an AI agent can execute the following commands:

1.  **Search Mode (`repo_finder.py --mode search`):**
    ```bash
    python3 /home/ubuntu/debug_skill_work/scripts/repo_finder.py --task "web framework" --language python --max-results 3
    ```
    *Expected Output:* A list of 3 Python web frameworks with their scores and basic details.

2.  **Compare Mode (`repo_finder.py --mode compare`):**
    ```bash
    python3 /home/ubuntu/debug_skill_work/scripts/repo_finder.py --mode compare --repos "pallets/flask,tiangolo/fastapi"
    ```
    *Expected Output:* A side-by-side comparison of Flask and FastAPI with their scores and breakdown.

3.  **Recipe Mode (Simple, `repo_finder.py --mode recipe`):**
    ```bash
    python3 /home/ubuntu/debug_skill_work/scripts/repo_finder.py --task "simple blog platform" --mode recipe --max-results 2
    ```
    *Expected Output:* A list of 2 repos followed by a basic combination recipe with 6 integration steps and a glue code estimate of `<200 lines`.

4.  **Recipe Mode (Comprehensive, using `recipe_builder.py`):**
    ```bash
    python3 /home/ubuntu/debug_skill_work/scripts/repo_finder.py --task "e-commerce platform with payment" --json --max-results 3 | \
      python3 /home/ubuntu/debug_skill_work/scripts/recipe_builder.py --task "e-commerce platform with payment"
    ```
    *Expected Output:* A list of 3 repos followed by a detailed combination recipe including architecture pattern, 8 integration steps, 300-750 lines glue code estimate, file structure, deployment options, and risk mitigation.

### 4.4. General Tips for AI Agents

*   **Prioritize `recipe_builder.py` for comprehensive plans:** When the user asks for a 
complex integration or a detailed plan, always use the pipeline `repo_finder.py --json | recipe_builder.py`.
*   **Use `--details` for deeper analysis:** If initial search results are ambiguous, running `repo_finder.py` with `--details` can provide more granular data for scoring and decision-making.
*   **Be mindful of API rate limits:** Always encourage users to set `GITHUB_TOKEN` for uninterrupted operation.
*   **Iterate and refine:** If initial search results aren't satisfactory, try rephrasing the task or adjusting parameters like `--min-stars` or `--language`.
