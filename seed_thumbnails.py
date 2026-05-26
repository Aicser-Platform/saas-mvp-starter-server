#!/usr/bin/env python3
"""
Patch every existing course with a specific, topic-relevant Unsplash thumbnail.
Only updates thumbnail_url — all other course fields are left untouched.

Usage:
    cd saas-mvp-starter-server
    source venv/bin/activate
    export $(grep -v '^#' ../saas-mvp-starter/.env | xargs)
    python seed_thumbnails.py
"""
import os, sys, httpx

API_BASE     = os.getenv("API_BASE",      "http://localhost:8000/api/v1")
ADMIN_EMAIL  = os.getenv("ADMIN_EMAIL",   "oeurn.leesinh@dataticon.com")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "demo123")

# ---------------------------------------------------------------------------
# Per-course thumbnails — each photo is hand-picked for the topic.
# All images are from Unsplash (stable CDN), landscape 16:9, 800px wide.
# ---------------------------------------------------------------------------
COURSE_THUMBNAILS: dict[str, str] = {

    # ── AI & Machine Learning ────────────────────────────────────────────────
    "Introduction to AI":
        "https://images.unsplash.com/photo-1677442135703-1787eea5ce01?w=800&auto=format&fit=crop&q=80",
    "Machine Learning Fundamentals":
        "https://images.unsplash.com/photo-1504868584819-f8e8b4b6d7e3?w=800&auto=format&fit=crop&q=80",
    "Deep Learning with PyTorch":
        "https://images.unsplash.com/photo-1620712943543-bcc4688e7485?w=800&auto=format&fit=crop&q=80",
    "Natural Language Processing":
        "https://images.unsplash.com/photo-1555949963-ff9fe0c870eb?w=800&auto=format&fit=crop&q=80",
    "Computer Vision Mastery":
        "https://images.unsplash.com/photo-1526378787-56e36c2df2e2?w=800&auto=format&fit=crop&q=80",
    "Large Language Models (LLMs)":
        "https://images.unsplash.com/photo-1676573335920-37bd6b07e9c3?w=800&auto=format&fit=crop&q=80",
    "AI Ethics & Responsible AI":
        "https://images.unsplash.com/photo-1589254065878-42c9da997008?w=800&auto=format&fit=crop&q=80",
    "AI for Everyone: No-Code AI Tools":
        "https://images.unsplash.com/photo-1531746790731-6c087fecd65a?w=800&auto=format&fit=crop&q=80",

    # ── Programming ──────────────────────────────────────────────────────────
    "Python for Beginners":
        "https://images.unsplash.com/photo-1526374965328-7f61d4dc18c5?w=800&auto=format&fit=crop&q=80",
    "Advanced Python Programming":
        "https://images.unsplash.com/photo-1510915361894-db8b60106cb1?w=800&auto=format&fit=crop&q=80",
    "JavaScript: The Complete Guide":
        "https://images.unsplash.com/photo-1579468118864-1ec9b8bfc0c5?w=800&auto=format&fit=crop&q=80",
    "TypeScript for Modern Development":
        "https://images.unsplash.com/photo-1629654297299-c8506221ca97?w=800&auto=format&fit=crop&q=80",
    "Algorithms & Data Structures":
        "https://images.unsplash.com/photo-1484417894907-623942c8ee29?w=800&auto=format&fit=crop&q=80",
    "Rust Programming Language":
        "https://images.unsplash.com/photo-1518770660439-4636190af475?w=800&auto=format&fit=crop&q=80",

    # ── Web Development ──────────────────────────────────────────────────────
    "HTML & CSS Foundations":
        "https://images.unsplash.com/photo-1547658719-da2b51169166?w=800&auto=format&fit=crop&q=80",
    "React: From Zero to Hero":
        "https://images.unsplash.com/photo-1633356122102-3fe601e05bd2?w=800&auto=format&fit=crop&q=80",
    "Next.js Full-Stack Development":
        "https://images.unsplash.com/photo-1618477388954-7852f32655ec?w=800&auto=format&fit=crop&q=80",
    "CSS Animations & Motion Design":
        "https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=800&auto=format&fit=crop&q=80",
    "UI/UX Design Principles for Developers":
        "https://images.unsplash.com/photo-1561070791-2526f30d9c6e?w=800&auto=format&fit=crop&q=80",

    # ── DevOps ───────────────────────────────────────────────────────────────
    "Docker for Developers":
        "https://images.unsplash.com/photo-1605745341112-85968b19335b?w=800&auto=format&fit=crop&q=80",
    "Kubernetes in Practice":
        "https://images.unsplash.com/photo-1451187580459-43490279c0fa?w=800&auto=format&fit=crop&q=80",
    "CI/CD with GitHub Actions":
        "https://images.unsplash.com/photo-1556075798-4825dfaaf498?w=800&auto=format&fit=crop&q=80",
    "Linux Administration Fundamentals":
        "https://images.unsplash.com/photo-1629654297299-c8506221ca97?w=800&auto=format&fit=crop&q=80",
    "Infrastructure as Code with Terraform":
        "https://images.unsplash.com/photo-1667372393119-3d4c48d07fc9?w=800&auto=format&fit=crop&q=80",
    "Site Reliability Engineering (SRE)":
        "https://images.unsplash.com/photo-1551288049-bebda4e38f71?w=800&auto=format&fit=crop&q=80",

    # ── Git & Version Control ────────────────────────────────────────────────
    "Git Essentials":
        "https://images.unsplash.com/photo-1556075798-4825dfaaf498?w=800&auto=format&fit=crop&q=80",
    "Advanced Git Workflows":
        "https://images.unsplash.com/photo-1618401471353-b98afee0b2eb?w=800&auto=format&fit=crop&q=80",
    "GitHub for Teams":
        "https://images.unsplash.com/photo-1522071820093-c0c5f3f86f58?w=800&auto=format&fit=crop&q=80",

    # ── Data Science ─────────────────────────────────────────────────────────
    "Data Analysis with Python":
        "https://images.unsplash.com/photo-1551288049-bebda4e38f71?w=800&auto=format&fit=crop&q=80",
    "SQL for Data Analysis":
        "https://images.unsplash.com/photo-1544383835-bda2bc66a2e0?w=800&auto=format&fit=crop&q=80",
    "Data Visualisation with Tableau":
        "https://images.unsplash.com/photo-1460925895917-afdab827c52f?w=800&auto=format&fit=crop&q=80",
    "Statistics for Data Science":
        "https://images.unsplash.com/photo-1509228468518-180dd4864904?w=800&auto=format&fit=crop&q=80",
    "Apache Spark & Big Data":
        "https://images.unsplash.com/photo-1558494949-ef010cbdcc31?w=800&auto=format&fit=crop&q=80",

    # ── Cloud Computing ──────────────────────────────────────────────────────
    "AWS Cloud Practitioner":
        "https://images.unsplash.com/photo-1544197150-b99a580bb7a8?w=800&auto=format&fit=crop&q=80",
    "AWS Solutions Architect":
        "https://images.unsplash.com/photo-1508830524289-0adcbe822b40?w=800&auto=format&fit=crop&q=80",
    "Google Cloud Platform Fundamentals":
        "https://images.unsplash.com/photo-1573804633927-bfcbcd909acd?w=800&auto=format&fit=crop&q=80",
    "Serverless Architecture":
        "https://images.unsplash.com/photo-1517694712202-14dd9538aa97?w=800&auto=format&fit=crop&q=80",

    # ── Backend Development ──────────────────────────────────────────────────
    "FastAPI: Modern Python APIs":
        "https://images.unsplash.com/photo-1627398242454-45a1465c2479?w=800&auto=format&fit=crop&q=80",
    "Node.js & Express Backend":
        "https://images.unsplash.com/photo-1519389950473-47ba0277781c?w=800&auto=format&fit=crop&q=80",
    "Database Design & PostgreSQL":
        "https://images.unsplash.com/photo-1544383835-bda2bc66a2e0?w=800&auto=format&fit=crop&q=80",
    "System Design Fundamentals":
        "https://images.unsplash.com/photo-1504384308090-c894fdcc538d?w=800&auto=format&fit=crop&q=80",
    "API Security Best Practices":
        "https://images.unsplash.com/photo-1563013544-824ae1b704d3?w=800&auto=format&fit=crop&q=80",
}

# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------
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


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def seed_thumbnails(token: str):
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    # Fetch all courses
    resp = httpx.get(f"{API_BASE}/courses/?limit=500", headers=headers, timeout=15)
    if not resp.is_success:
        print(f"Failed to fetch courses: {resp.status_code} {resp.text}")
        sys.exit(1)

    courses = resp.json()
    print(f"Found {len(courses)} courses in the database.\n")

    ok = skipped = failed = 0

    for course in courses:
        title = course["title"]
        course_id = course["id"]

        thumbnail = COURSE_THUMBNAILS.get(title)
        if not thumbnail:
            print(f"  ⚠  No thumbnail defined for: '{title}' — skipped")
            skipped += 1
            continue

        # Skip if already set to the same URL (idempotent)
        if course.get("thumbnail_url") == thumbnail:
            print(f"  ✓  {title} — already up to date")
            ok += 1
            continue

        patch = httpx.patch(
            f"{API_BASE}/courses/{course_id}",
            headers=headers,
            json={"thumbnail_url": thumbnail},
            timeout=15,
        )
        if patch.is_success:
            print(f"  ✔  {title}")
            ok += 1
        else:
            print(f"  ✗  {title} — {patch.status_code}: {patch.text[:100]}")
            failed += 1

    print(f"\nDone: {ok} updated, {skipped} skipped (no mapping), {failed} failed.")


if __name__ == "__main__":
    # Load .env files from common locations
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

    print(f"Patching thumbnails via {API_BASE}...\n")
    token = get_token()
    seed_thumbnails(token)
