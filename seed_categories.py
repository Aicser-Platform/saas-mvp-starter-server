#!/usr/bin/env python3
"""
Seed the categories table from the 8 canonical category names used in courses.

Usage:
    cd saas-mvp-starter-server
    source venv/bin/activate
    python seed_categories.py
"""

import os
import sys
import httpx

API_BASE       = os.getenv("API_BASE", "http://localhost:8000/api/v1")
ADMIN_EMAIL    = os.getenv("ADMIN_EMAIL", "oeurn.leesinh@dataticon.com")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "demo123")

CATEGORIES = [
    {"name": "AI & Machine Learning",  "description": "Artificial intelligence, ML algorithms, deep learning, NLP, and computer vision."},
    {"name": "Programming",            "description": "Core programming languages, algorithms, data structures, and software engineering fundamentals."},
    {"name": "Web Development",        "description": "Frontend and full-stack web technologies including HTML, CSS, JavaScript, React, and Next.js."},
    {"name": "DevOps",                 "description": "Docker, Kubernetes, CI/CD pipelines, Linux administration, and infrastructure as code."},
    {"name": "Git & Version Control",  "description": "Git workflows, branching strategies, collaboration, and version control best practices."},
    {"name": "Data Science",           "description": "Data analysis, SQL, visualisation, statistics, and big data processing with Python and Spark."},
    {"name": "Cloud Computing",        "description": "AWS, Google Cloud, serverless architecture, and cloud-native application design."},
    {"name": "Backend Development",    "description": "REST APIs, databases, system design, authentication, and backend frameworks."},
]


def load_env():
    for env_path in [
        os.path.join(os.path.dirname(__file__), ".env"),
        os.path.join(os.path.dirname(__file__), "..", "saas-mvp-starter", ".env.local"),
        os.path.join(os.path.dirname(__file__), "..", "saas-mvp-starter", ".env"),
    ]:
        if os.path.exists(env_path):
            with open(env_path) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, _, v = line.partition("=")
                        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def get_token() -> str:
    supabase_url = os.getenv("NEXT_PUBLIC_SUPABASE_URL", "")
    anon_key     = os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY", "")
    if not supabase_url or not anon_key:
        print("ERROR: Set NEXT_PUBLIC_SUPABASE_URL and NEXT_PUBLIC_SUPABASE_ANON_KEY")
        sys.exit(1)
    if not ADMIN_PASSWORD:
        print("ERROR: Set ADMIN_PASSWORD")
        sys.exit(1)

    resp = httpx.post(
        f"{supabase_url}/auth/v1/token?grant_type=password",
        headers={"apikey": anon_key, "Content-Type": "application/json"},
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
        timeout=15,
    )
    if resp.status_code != 200:
        print(f"Auth failed: {resp.status_code} {resp.text}")
        sys.exit(1)
    return resp.json()["access_token"]


def fetch_existing(token: str) -> set[str]:
    resp = httpx.get(
        f"{API_BASE}/categories/",
        headers={"Authorization": f"Bearer {token}"},
        timeout=15,
    )
    if not resp.is_success:
        print(f"Failed to fetch existing categories: {resp.status_code}")
        return set()
    return {c["name"] for c in resp.json()}


def create_category(token: str, name: str, description: str) -> bool:
    resp = httpx.post(
        f"{API_BASE}/categories/",
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        json={"name": name, "description": description},
        timeout=15,
    )
    return resp.is_success


def main():
    load_env()
    print(f"Connecting to {API_BASE}...")
    token = get_token()

    existing = fetch_existing(token)
    print(f"Found {len(existing)} existing categories\n")

    created = skipped = failed = 0

    for cat in CATEGORIES:
        if cat["name"] in existing:
            print(f"  ↷  {cat['name']}  [already exists, skipped]")
            skipped += 1
            continue

        ok = create_category(token, cat["name"], cat["description"])
        if ok:
            print(f"  ✓  {cat['name']}")
            created += 1
        else:
            print(f"  ✗  {cat['name']}  [failed]")
            failed += 1

    print(f"\nDone: {created} created, {skipped} skipped, {failed} failed.")


if __name__ == "__main__":
    main()
