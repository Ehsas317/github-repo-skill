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


def github_api_get(endpoint: str, params: dict = None, expected_type=dict) -> dict:
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
        return expected_type()
    except Exception as e:
        print(f"[!] Request failed: {e}", file=sys.stderr)
        return expected_type()


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

    contributors_data = github_api_get(f"/repos/{owner}/{repo}/contributors", expected_type=list)
    contributors = contributors_data if isinstance(contributors_data, list) and contributors_data else []

    # Get last 100 commits for activity analysis
    recent_commits_data = github_api_get(
        f"/repos/{owner}/{repo}/commits",
        {"per_page": 100},
        expected_type=list
    )
    recent_commits = recent_commits_data if isinstance(recent_commits_data, list) and recent_commits_data else []

    details["_recent_commit_count"] = len(recent_commits)
    details["_contributor_count"] = len(contributors)

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
        "c++": "c++", "c#": "c#", "csharp": "c#", "php": "php",
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
        queries.append(f"websocket chat server {'language:' + language if language else ''}".strip())
    if any(w in words for w in ["auth", "login", "authentication", "oauth", "jwt"]):
        queries.append(f"authentication jwt oauth {'language:' + language if language else ''}".strip())
    if any(w in words for w in ["payment", "stripe", "billing", "subscription"]):
        queries.append(f"payment processing stripe {'language:' + language if language else ''}".strip())
    if any(w in words for w in ["ai", "ml", "machine", "learning", "llm", "gpt"]):
        queries.append(f"llm ai integration {'language:' + language if language else ''}".strip())

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
            "role": f"Component {i}: {repo['description'][:80] if repo['description'] else 'No description'}"
        })

    # Generate integration strategy
    langs = [r["language"] for r in selected if r["language"]]
    primary_lang = max(set(langs), key=langs.count) if langs else "your language"

    recipe["integration_strategy"] = (
        f"1. Clone/fork the selected repositories\n"
        f"2. Identify the API boundaries and data contracts\n"
        f"3. Create a thin orchestration layer in {primary_lang or 'your preferred language'}\n"
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
        f"Instead of writing full implementations, import from: {[r['full_name'] for r in selected[:3]]}",
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
