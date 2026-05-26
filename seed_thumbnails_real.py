#!/usr/bin/env python3
"""
Download real JPEG/PNG thumbnails and upload them to Azure Blob Storage,
then patch each course's thumbnail_url with the self-hosted /api/v1/files/... URL.

Usage:
    cd saas-mvp-starter-server
    source venv/bin/activate
    python seed_thumbnails_real.py           # skip courses already self-hosted
    python seed_thumbnails_real.py --force   # re-upload everything
"""

import os
import sys
import mimetypes
import argparse
import httpx

API_BASE    = os.getenv("API_BASE", "http://localhost:8000/api/v1")
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "oeurn.leesinh@dataticon.com")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "demo123")

# Derive origin so relative URLs (/api/v1/files/...) can be made absolute
API_HOST = API_BASE.split("/api/")[0]  # e.g. http://localhost:8000

# ---------------------------------------------------------------------------
# Pexels CDN — direct JPEG downloads, no API key required
# Format: https://images.pexels.com/photos/{id}/pexels-photo-{id}.jpeg?...
# ---------------------------------------------------------------------------
_PX = "https://images.pexels.com/photos/{id}/pexels-photo-{id}.jpeg?auto=compress&cs=tinysrgb&w=800&h=450&fit=crop"

def px(photo_id: int) -> str:
    return _PX.format(id=photo_id)


# ---------------------------------------------------------------------------
# Per-course thumbnail map  (course title → Pexels image URL)
# ---------------------------------------------------------------------------
THUMBNAILS: dict[str, str] = {
    # ── AI & Machine Learning ────────────────────────────────────────────────
    "Introduction to AI":                      px(8386434),
    "Machine Learning Fundamentals":           px(8386440),
    "Deep Learning with PyTorch":              px(8386423),
    "Natural Language Processing":             px(4050291),
    "Computer Vision Mastery":                 px(1366957),
    "Large Language Models (LLMs)":            px(8849295),
    "AI Ethics & Responsible AI":              px(3184465),
    "AI for Everyone: No-Code AI Tools":       px(3861969),

    # ── Programming ──────────────────────────────────────────────────────────
    "Python for Beginners":                    px(1181671),
    "Advanced Python Programming":             px(574071),
    "JavaScript: The Complete Guide":          px(4709285),
    "TypeScript for Modern Development":       px(11035471),
    "Algorithms & Data Structures":            px(546819),
    "Rust Programming Language":               px(270348),

    # ── Web Development ───────────────────────────────────────────────────────
    "HTML & CSS Foundations":                  px(326503),
    "React: From Zero to Hero":                px(11035380),
    "Next.js Full-Stack Development":          px(3861984),
    "CSS Animations & Motion Design":          px(1762851),
    "UI/UX Design Principles for Developers":  px(196644),

    # ── DevOps ───────────────────────────────────────────────────────────────
    "Docker for Developers":                   px(1148820),
    "Kubernetes in Practice":                  px(325111),
    "CI/CD with GitHub Actions":               px(1181244),
    "Linux Administration Fundamentals":       px(207580),
    "Infrastructure as Code with Terraform":   px(2004161),
    "Site Reliability Engineering (SRE)":      px(1181354),

    # ── Git & Version Control ────────────────────────────────────────────────
    "Git Essentials":                          px(4164418),
    "Advanced Git Workflows":                  px(3861972),
    "GitHub for Teams":                        px(1181675),

    # ── Data Science ─────────────────────────────────────────────────────────
    "Data Analysis with Python":               px(669615),
    "SQL for Data Analysis":                   px(574069),
    "Data Visualisation with Tableau":         px(590022),
    "Statistics for Data Science":             px(3862132),
    "Apache Spark & Big Data":                 px(373543),

    # ── Cloud Computing ───────────────────────────────────────────────────────
    "AWS Cloud Practitioner":                  px(1181316),
    "AWS Solutions Architect":                 px(3183150),
    "Google Cloud Platform Fundamentals":      px(7988079),
    "Serverless Architecture":                 px(1181291),

    # ── Backend Development ───────────────────────────────────────────────────
    "FastAPI: Modern Python APIs":             px(1181676),
    "Node.js & Express Backend":               px(4709284),
    "Database Design & PostgreSQL":            px(1181243),
    "System Design Fundamentals":              px(3861974),
    "API Security Best Practices":             px(60504),
}

# Fallback images per category (used when course title not in THUMBNAILS)
CATEGORY_FALLBACKS: dict[str, str] = {
    "AI & Machine Learning":   px(8386434),
    "Programming":             px(1181671),
    "Web Development":         px(326503),
    "DevOps":                  px(1148820),
    "Git & Version Control":   px(4164418),
    "Data Science":            px(669615),
    "Cloud Computing":         px(2004161),
    "Backend Development":     px(1181676),
}

GENERIC_FALLBACK = px(1181671)  # generic coding photo


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
# Course fetching
# ---------------------------------------------------------------------------
def fetch_courses(token: str) -> list[dict]:
    resp = httpx.get(
        f"{API_BASE}/courses/?limit=500",
        headers={"Authorization": f"Bearer {token}"},
        timeout=15,
    )
    if not resp.is_success:
        print(f"Failed to fetch courses: {resp.status_code}")
        sys.exit(1)
    return resp.json()


# ---------------------------------------------------------------------------
# Image download
# ---------------------------------------------------------------------------
def download_image(url: str) -> tuple[bytes, str, str]:
    """
    Download an image from url.
    Returns (bytes, mime_type, file_extension).
    Raises httpx.HTTPError on failure.
    """
    resp = httpx.get(url, follow_redirects=True, timeout=30)
    resp.raise_for_status()

    content_type = resp.headers.get("content-type", "image/jpeg").split(";")[0].strip()

    # Map MIME to extension
    ext_map = {
        "image/jpeg": ".jpg",
        "image/jpg":  ".jpg",
        "image/png":  ".png",
        "image/webp": ".webp",
        "image/gif":  ".gif",
    }
    ext = ext_map.get(content_type, mimetypes.guess_extension(content_type) or ".jpg")

    # Fallback: if server returns wrong content type for Pexels, assume JPEG
    if content_type not in ext_map:
        content_type = "image/jpeg"
        ext = ".jpg"

    return resp.content, content_type, ext


# ---------------------------------------------------------------------------
# Upload to FastAPI /api/v1/lessons/upload
# ---------------------------------------------------------------------------
def upload_image(token: str, img_bytes: bytes, mime_type: str, filename: str) -> str:
    """
    Upload image bytes via multipart/form-data.
    Returns the thumbnail_url to store (absolute URL).
    """
    resp = httpx.post(
        f"{API_BASE}/lessons/upload",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": (filename, img_bytes, mime_type)},
        timeout=60,
    )
    if not resp.is_success:
        raise RuntimeError(f"Upload failed {resp.status_code}: {resp.text[:120]}")

    data = resp.json()
    url: str = data.get("url", "")

    # Make relative URLs absolute so the browser can resolve them from any origin
    if url.startswith("/"):
        url = f"{API_HOST}{url}"

    return url


# ---------------------------------------------------------------------------
# Patch course thumbnail
# ---------------------------------------------------------------------------
def patch_thumbnail(token: str, course_id: str, thumbnail_url: str) -> bool:
    resp = httpx.patch(
        f"{API_BASE}/courses/{course_id}",
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        json={"thumbnail_url": thumbnail_url},
        timeout=15,
    )
    return resp.is_success


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="Seed real JPEG thumbnails for all courses")
    parser.add_argument("--force", action="store_true", help="Re-upload even already self-hosted thumbnails")
    args = parser.parse_args()

    # Load .env files (same logic as seed_courses.py)
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

    print(f"Connecting to {API_BASE}...")
    token = get_token()
    courses = fetch_courses(token)
    print(f"Found {len(courses)} courses\n")

    ok = skipped = failed = 0

    for course in courses:
        title    = course.get("title", "")
        cid      = course.get("id", "")
        category = course.get("category") or ""
        existing = course.get("thumbnail_url") or ""

        # Skip if already self-hosted (uploaded through our API) and not --force
        if not args.force and (
            f"{API_HOST}/api/v1/files/" in existing or
            f"{API_HOST}/uploads/" in existing
        ):
            print(f"  ↷  {title}  [already self-hosted, skipped]")
            skipped += 1
            continue

        # Resolve image source URL
        source_url = THUMBNAILS.get(title) or CATEGORY_FALLBACKS.get(category) or GENERIC_FALLBACK

        try:
            # 1. Download
            img_bytes, mime_type, ext = download_image(source_url)
            # Sanitise filename: lowercase, replace spaces with dashes
            safe_title = title.lower().replace(" ", "-").replace("/", "-")[:40]
            filename = f"{safe_title}{ext}"

            # 2. Upload to Azure / local
            thumbnail_url = upload_image(token, img_bytes, mime_type, filename)

            # 3. Patch course record
            success = patch_thumbnail(token, cid, thumbnail_url)
            if success:
                print(f"  ✓  {title}")
                print(f"     → {thumbnail_url}")
                ok += 1
            else:
                print(f"  ✗  {title}  [PATCH failed]")
                failed += 1

        except httpx.HTTPStatusError as e:
            print(f"  ✗  {title}  [download error: {e.response.status_code} from {source_url[:60]}]")
            failed += 1
        except Exception as e:
            print(f"  ✗  {title}  [{e}]")
            failed += 1

    print(f"\nDone: {ok} uploaded, {skipped} skipped, {failed} failed.")


if __name__ == "__main__":
    main()
