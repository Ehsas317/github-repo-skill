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
