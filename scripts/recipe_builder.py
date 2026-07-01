#!/usr/bin/env python3
"""
Recipe Builder - Generate combination recipes from discovered repositories.

Reads repo_finder.py JSON output and creates actionable integration guides.

Usage:
    python repo_finder.py --task "chat app" --json | python recipe_builder.py --task "chat app"
    python recipe_builder.py --repos-file repos.json --task "e-commerce platform"
    python recipe_builder.py --repos "socketio/socket.io,auth0/node-jsonwebtoken,stripe/stripe-node"
    python recipe_builder.py --task "task" --vibe  # Vibe coding mode
"""

import argparse
import json
import sys
import os
from typing import List, Dict, Any

# ─── VIBE MODE: AI-AGENT-OPTIMIZED OUTPUT ─────────────────────────────────────

VIBE_CHECK_EMOJI = {
    "drop-in": "✅",
    "needs-key": "🔑",
    "needs-config": "⚙️",
    "docker-ready": "🐳",
    "manual-setup": "📦",
}


def vibe_check(repo: Dict[str, Any]) -> str:
    """One-line vibe check for AI agents."""
    desc = (repo.get("description") or "").lower()
    name = repo.get("full_name", "")
    
    if "docker" in desc or "container" in desc:
        return f"{VIBE_CHECK_EMOJI['docker-ready']} Docker-ready. Copy-paste compose."
    if any(k in desc for k in ["api key", "apikey", "token", "auth"]):
        return f"{VIBE_CHECK_EMOJI['needs-key']} Needs API key. 5-min setup."
    if "sdk" in desc or "client" in desc:
        return f"{VIBE_CHECK_EMOJI['drop-in']} Drop-in SDK. Import and go."
    if "framework" in desc or "framework" in name.lower():
        return f"{VIBE_CHECK_EMOJI['needs-config']} Framework. Needs config hook."
    return f"{VIBE_CHECK_EMOJI['drop-in']} Drop-in. No config needed."


def generate_docker_compose(repos: List[Dict[str, Any]], task: str) -> str:
    """Generate a copy-paste ready docker-compose.yml."""
    services = {}
    for i, repo in enumerate(repos):
        name = repo.get("full_name", "").split("/")[-1].lower().replace("-", "_")
        port = 8000 + i
        services[name] = {
            "image": f"{repo.get('full_name', 'service').lower()}:latest",
            "container_name": f"{name}_{i}",
            "ports": [f"{port}:{port}"],
            "restart": "unless-stopped",
            "environment": [f"PORT={port}"],
        }
    
    # Add an orchestrator service
    services["app"] = {
        "build": ".",
        "container_name": "app",
        "depends_on": list(services.keys()),
        "env_file": [".env"],
        "volumes": [".:/app"],
    }
    
    compose = {
        "version": "3.8",
        "services": services
    }
    return json.dumps(compose, indent=2)


def generate_vibe_main(repos: List[Dict[str, Any]], task: str) -> str:
    """Generate a main.py skeleton with explicit TODO markers."""
    imports = []
    adapters = []
    setup_lines = []
    
    for i, repo in enumerate(repos):
        name = repo.get("full_name", "").split("/")[-1].lower().replace("-", "_")
        class_name = "".join([x.capitalize() for x in name.split("_")])
        
        imports.append(f"from adapters.{name} import {class_name}Adapter")
        adapters.append(f"{name}_svc = {class_name}Adapter()")
        setup_lines.append(f"    # TODO: Configure {name} ({repo.get('html_url')})")
        
    code = f'''# main.py — Auto-generated for: {task}
# DO NOT EDIT REPO INTERNALS. Use adapters only.

{chr(10).join(imports)}

{chr(10).join(adapters)}

def run():
{chr(10).join(setup_lines)}
    # TODO: Add your business logic here
    pass

if __name__ == "__main__":
    run()'''
    return code


def generate_env_template(repos: List[Dict[str, Any]]) -> str:
    """Generate .env with TODO markers for every likely API key."""
    lines = ["# .env — Auto-generated. Fill in before running."]
    seen = set()
    
    for repo in repos:
        name = repo.get("full_name", "").split("/")[-1].upper().replace("-", "_")
        if name not in seen:
            seen.add(name)
            lines.append(f"{name}_API_KEY=TODO_FILL_ME_IN")
    
    lines.append("GITHUB_TOKEN=TODO_OPTIONAL_FOR_RATE_LIMITS")
    return "\n".join(lines)


def generate_vibe_recipe(repos: List[Dict[str, Any]], task: str) -> Dict[str, Any]:
    """Generate a token-minimal, code-first recipe for AI vibe coding."""
    if not repos:
        return {"task": task, "status": "NO_REPOS", "code": {}}
    
    repos.sort(key=lambda x: x.get("score", x.get("stars", 0)), reverse=True)
    selected = []
    for i, repo in enumerate(repos):
        selected.append({
            "rank": i + 1,
            "name": repo["full_name"],
            "url": repo["html_url"],
            "vibe": vibe_check(repo),
            "role": f"Component {i+1} for {task}",
            "language": repo.get("language"),
            "score": repo.get("score", 0),
        })
        
    return {
        "task": task,
        "status": "READY",
        "philosophy": "Compose, don't build. Adapters only. No repo internals.",
        "selected": selected,
        "code": {
            "docker-compose.yml": generate_docker_compose(repos, task),
            "main.py": generate_vibe_main(repos, task),
            ".env": generate_env_template(repos),
        },
        "next_steps": [
            "1. Copy code blocks into your project.",
            "2. Fill TODOs in .env.",
            "3. Run `docker-compose up`.",
            "4. Write adapters in src/adapters/.",
        ],
        "token_note": "Load only adapter interfaces, not full repo source.",
    }


def print_vibe_recipe(recipe: Dict[str, Any]):
    """Ultra-minimal output. No prose. Just code blocks and JSON."""
    if recipe.get("status") == "NO_REPOS":
        print('{"error": "No repos found"}')
        return

    # Machine-readable header
    print(f"# TASK: {recipe['task']}")
    print(f"# PHILOSOPHY: {recipe['philosophy']}")
    print()

    # Selected repos — one line each
    for r in recipe["selected"]:
        print(f"# [{r['rank']}] {r['name']} — {r['vibe']} — {r['url']}")
    print()

    print("# ─── CODE BLOCKS — COPY PASTE ───")
    print()
    for filename, content in recipe["code"].items():
        print(f"### {filename}")
        print("```")
        print(content)
        print("```")
        print()

    print("# ─── NEXT STEPS ───")
    for step in recipe["next_steps"]:
        print(f"# {step}")
    print()
    print(f"# {recipe['token_note']}")


# ─── EXISTING RECIPE BUILDER CODE ───────────────────────────────────────────

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
    has_frontend = any(t in topics for t in ["react", "vue", "angular", "frontend", "ui"])
    has_backend = any(t in topics for t in ["backend", "server", "api", "rest"])
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
            "license": repo.get("license"),
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

    # AI agent notes
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
        print(f"      License: {repo['license'] or 'N/A'}")
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
    parser.add_argument("--vibe", action="store_true", help="Vibe coding mode: code-first, minimal prose, copy-paste ready")

    args = parser.parse_args()

    repos = []

    if args.repos_file:
        with open(args.repos_file) as f:
            repos = json.load(f)
    elif args.repos:
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

    if args.vibe:
        recipe = generate_vibe_recipe(repos, args.task)
        if args.json:
            print(json.dumps(recipe, indent=2))
        else:
            print_vibe_recipe(recipe)
    else:
        recipe = generate_combination_recipe(repos, args.task)
        if args.json:
            print(json.dumps(recipe, indent=2))
        else:
            print_recipe(recipe)


if __name__ == "__main__":
    main()
