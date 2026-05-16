#!/usr/bin/env python3
"""
Seed courses (with mixed tiers, real thumbnails, and lessons) into local FastAPI.
Usage:
    cd saas-mvp-starter-server
    source venv/bin/activate
    export $(grep -v '^#' ../saas-mvp-starter/.env | xargs)
    python seed_courses.py
"""
import os, sys, httpx

API_BASE = os.getenv("API_BASE", "http://localhost:8000/api/v1")
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "oeurn.leesinh@dataticon.com")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "demo123")

# ---------------------------------------------------------------------------
# Thumbnail helpers (Unsplash Source – stable CDN URLs)
# ---------------------------------------------------------------------------
THUMBS = {
    "AI & Machine Learning": "https://images.unsplash.com/photo-1677442135703-1787eea5ce01?w=800&auto=format&fit=crop",
    "Programming":           "https://images.unsplash.com/photo-1542831371-29b0f74f9713?w=800&auto=format&fit=crop",
    "Web Development":       "https://images.unsplash.com/photo-1547658719-da2b51169166?w=800&auto=format&fit=crop",
    "DevOps":                "https://images.unsplash.com/photo-1667372393119-3d4c48d07fc9?w=800&auto=format&fit=crop",
    "Git & Version Control": "https://images.unsplash.com/photo-1556075798-4825dfaaf498?w=800&auto=format&fit=crop",
    "Data Science":          "https://images.unsplash.com/photo-1551288049-bebda4e38f71?w=800&auto=format&fit=crop",
    "Cloud Computing":       "https://images.unsplash.com/photo-1544197150-b99a580bb7a8?w=800&auto=format&fit=crop",
    "Backend Development":   "https://images.unsplash.com/photo-1627398242454-45a1465c2479?w=800&auto=format&fit=crop",
}

# ---------------------------------------------------------------------------
# Lesson templates  (title, content summary, YouTube video id, resources)
# ---------------------------------------------------------------------------
def make_lessons(course_id: str, topic: str):
    """Return a list of lesson payloads for a course."""
    base = [
        {
            "course_id": course_id,
            "title": f"Welcome to {topic}",
            "content": f"In this opening lesson you will get a full overview of what {topic} is, why it matters, and what you will build by the end of the course. We cover the prerequisites and set up your local development environment.",
            "video_url": "https://www.youtube.com/embed/aircAruvnKk",   # 3Blue1Brown - Neural Nets
            "order_index": 0,
            "resources": [
                {"title": "Course Slides (PDF)", "url": "https://example.com/slides.pdf", "type": "pdf"},
                {"title": "Official Docs", "url": "https://docs.example.com", "type": "link"},
            ],
        },
        {
            "course_id": course_id,
            "title": "Core Concepts & Terminology",
            "content": f"Deep dive into the foundational concepts of {topic}. We break down key terminology and mental models that will help you throughout the course.",
            "video_url": "https://www.youtube.com/embed/Ilg3gGewQ5U",   # Google ML crash course
            "order_index": 1,
            "resources": [
                {"title": "Cheat Sheet", "url": "https://example.com/cheatsheet.pdf", "type": "pdf"},
            ],
        },
        {
            "course_id": course_id,
            "title": "Hands-On: Your First Project",
            "content": "Time to get your hands dirty. Follow along as we build a real mini-project from scratch, applying everything learned so far.",
            "video_url": "https://www.youtube.com/embed/rfscVS0vtbw",   # CS50 Intro
            "order_index": 2,
            "resources": [
                {"title": "Starter Code (GitHub)", "url": "https://github.com/example/starter", "type": "link"},
            ],
        },
        {
            "course_id": course_id,
            "title": "Intermediate Techniques",
            "content": "Level up with intermediate patterns and best practices. We look at common pitfalls and how professionals solve them.",
            "video_url": "https://www.youtube.com/embed/HXV3zeQKqGY",   # SQL full course
            "order_index": 3,
            "resources": [
                {"title": "Reference Manual", "url": "https://example.com/manual.pdf", "type": "pdf"},
            ],
        },
        {
            "course_id": course_id,
            "title": "Real-World Case Study",
            "content": "Walk through a real-world case study used in production. Understand architecture decisions and trade-offs.",
            "video_url": "https://www.youtube.com/embed/W6NZfCO5SIk",   # JavaScript crash course
            "order_index": 4,
            "resources": [
                {"title": "Case Study PDF", "url": "https://example.com/case-study.pdf", "type": "pdf"},
                {"title": "Discussion Forum", "url": "https://community.example.com", "type": "link"},
            ],
        },
        {
            "course_id": course_id,
            "title": "Advanced Topics & Optimisation",
            "content": "Explore advanced topics: performance tuning, scalability patterns, and production readiness. Suitable for those who want to go beyond the basics.",
            "video_url": "https://www.youtube.com/embed/zOjov-2OZ0E",   # Python tutorial
            "order_index": 5,
            "resources": [
                {"title": "Advanced Guide", "url": "https://example.com/advanced.pdf", "type": "pdf"},
            ],
        },
        {
            "course_id": course_id,
            "title": "Final Project & Next Steps",
            "content": "Put it all together in a capstone project. We also cover what to learn next and how to continue growing in this field.",
            "video_url": "https://www.youtube.com/embed/bMknfKXIFA8",   # Python for beginners
            "order_index": 6,
            "resources": [
                {"title": "Certificate Template", "url": "https://example.com/cert.pdf", "type": "pdf"},
                {"title": "Community Slack", "url": "https://slack.example.com", "type": "link"},
            ],
        },
    ]
    return base

# ---------------------------------------------------------------------------
# Course catalogue  – mixed tiers
# ---------------------------------------------------------------------------
COURSES = [
    # AI & Machine Learning
    {"title":"Introduction to AI","description":"Learn the basics of Artificial Intelligence and machine learning concepts.","content":"Covers supervised/unsupervised learning, neural networks, and real-world AI applications.","difficulty":"beginner","required_tier":"free","category":"AI & Machine Learning"},
    {"title":"Machine Learning Fundamentals","description":"Master essential ML algorithms from linear regression to random forests.","content":"Hands-on intro with scikit-learn, model evaluation, and feature engineering.","difficulty":"intermediate","required_tier":"pro","category":"AI & Machine Learning"},
    {"title":"Deep Learning with PyTorch","description":"Build neural networks from scratch using PyTorch.","content":"CNNs, RNNs, LSTMs, and transformers. Real projects from image classification to text generation.","difficulty":"advanced","required_tier":"pro","category":"AI & Machine Learning"},
    {"title":"Natural Language Processing","description":"Master NLP techniques from tokenisation to transformer models.","content":"NLTK, spaCy, Hugging Face transformers, and sentiment analysis.","difficulty":"intermediate","required_tier":"pro","category":"AI & Machine Learning"},
    {"title":"Computer Vision Mastery","description":"Build image processing applications with OpenCV and deep learning.","content":"Object detection, image segmentation, and real-time video processing.","difficulty":"advanced","required_tier":"premium","category":"AI & Machine Learning"},
    {"title":"Large Language Models (LLMs)","description":"Understand and fine-tune large language models like GPT and LLaMA.","content":"Prompt engineering, fine-tuning with LoRA, RAG pipelines, and production LLM apps.","difficulty":"advanced","required_tier":"premium","category":"AI & Machine Learning"},
    {"title":"AI Ethics & Responsible AI","description":"Understand the ethical implications and societal impact of AI systems.","content":"Fairness, accountability, transparency, and privacy in AI.","difficulty":"beginner","required_tier":"free","category":"AI & Machine Learning"},
    {"title":"AI for Everyone: No-Code AI Tools","description":"Use AI tools without writing a single line of code.","content":"ChatGPT, Midjourney, Notion AI, and automation platforms.","difficulty":"beginner","required_tier":"free","category":"AI & Machine Learning"},
    # Programming
    {"title":"Python for Beginners","description":"Start your programming journey with Python.","content":"Python syntax, data types, functions, loops, and file handling.","difficulty":"beginner","required_tier":"free","category":"Programming"},
    {"title":"Advanced Python Programming","description":"Level up with decorators, generators, async/await, and metaprogramming.","content":"Advanced Python patterns used in production codebases.","difficulty":"advanced","required_tier":"pro","category":"Programming"},
    {"title":"JavaScript: The Complete Guide","description":"From basic syntax to modern ES2024 features.","content":"Closures, promises, async/await, modules, and browser APIs.","difficulty":"beginner","required_tier":"free","category":"Programming"},
    {"title":"TypeScript for Modern Development","description":"Add type safety to your JavaScript projects.","content":"Generics, interfaces, decorators, and integration with React and Node.js.","difficulty":"intermediate","required_tier":"pro","category":"Programming"},
    {"title":"Algorithms & Data Structures","description":"Crack coding interviews and write efficient code.","content":"Arrays, linked lists, trees, graphs, sorting, searching, and dynamic programming.","difficulty":"intermediate","required_tier":"pro","category":"Programming"},
    {"title":"Rust Programming Language","description":"Learn the modern systems programming language loved for safety and speed.","content":"Ownership, borrowing, lifetimes, concurrency, and WebAssembly modules.","difficulty":"advanced","required_tier":"premium","category":"Programming"},
    # Web Development
    {"title":"HTML & CSS Foundations","description":"Build your first website with HTML5 and modern CSS.","content":"Semantic HTML, flexbox, CSS Grid, responsive design, and accessibility.","difficulty":"beginner","required_tier":"free","category":"Web Development"},
    {"title":"React: From Zero to Hero","description":"Build dynamic user interfaces with React 18 and hooks.","content":"Components, state, props, context API, React Router, and scalable patterns.","difficulty":"intermediate","required_tier":"pro","category":"Web Development"},
    {"title":"Next.js Full-Stack Development","description":"Build production-ready full-stack apps with Next.js 14.","content":"Server components, server actions, authentication, Prisma, and Vercel deployment.","difficulty":"intermediate","required_tier":"pro","category":"Web Development"},
    {"title":"CSS Animations & Motion Design","description":"Create stunning animations that delight users.","content":"CSS keyframes, transitions, transforms, Framer Motion, and GSAP.","difficulty":"intermediate","required_tier":"pro","category":"Web Development"},
    {"title":"UI/UX Design Principles for Developers","description":"Learn design thinking to build beautiful and usable interfaces.","content":"Colour theory, typography, spacing, accessibility, and Figma-to-code.","difficulty":"beginner","required_tier":"free","category":"Web Development"},
    # DevOps
    {"title":"Docker for Developers","description":"Containerise your applications with Docker.","content":"Images, containers, volumes, networking, and Docker Compose.","difficulty":"beginner","required_tier":"free","category":"DevOps"},
    {"title":"Kubernetes in Practice","description":"Orchestrate containers at scale with Kubernetes.","content":"Pods, services, deployments, ingress, and Helm charts.","difficulty":"advanced","required_tier":"pro","category":"DevOps"},
    {"title":"CI/CD with GitHub Actions","description":"Automate your build, test, and deploy pipelines.","content":"End-to-end CI/CD with GitHub Actions. Secrets management, matrix builds.","difficulty":"intermediate","required_tier":"pro","category":"DevOps"},
    {"title":"Linux Administration Fundamentals","description":"Master the Linux command line for DevOps and server management.","content":"File system, permissions, process management, shell scripting, networking.","difficulty":"beginner","required_tier":"free","category":"DevOps"},
    {"title":"Infrastructure as Code with Terraform","description":"Provision and manage cloud infrastructure using code.","content":"Terraform HCL, modules, state management, AWS/GCP/Azure deployment.","difficulty":"advanced","required_tier":"premium","category":"DevOps"},
    {"title":"Site Reliability Engineering (SRE)","description":"Apply Google's SRE principles to build reliable systems.","content":"SLOs, SLIs, error budgets, on-call practices, postmortems, chaos engineering.","difficulty":"advanced","required_tier":"premium","category":"DevOps"},
    # Git & Version Control
    {"title":"Git Essentials","description":"Learn version control with Git from scratch.","content":"Commits, branches, merging, rebasing, and GitHub collaboration.","difficulty":"beginner","required_tier":"free","category":"Git & Version Control"},
    {"title":"Advanced Git Workflows","description":"Master branching strategies and team collaboration patterns.","content":"Git Flow, trunk-based development, interactive rebase, cherry-pick, bisect.","difficulty":"intermediate","required_tier":"pro","category":"Git & Version Control"},
    {"title":"GitHub for Teams","description":"Collaborate on open-source and private projects with GitHub.","content":"Pull requests, code reviews, GitHub Projects, Actions, security scanning.","difficulty":"intermediate","required_tier":"pro","category":"Git & Version Control"},
    # Data Science
    {"title":"Data Analysis with Python","description":"Analyse and visualise data using pandas and matplotlib.","content":"Load, clean, transform, and visualise datasets. pandas, NumPy, seaborn.","difficulty":"beginner","required_tier":"free","category":"Data Science"},
    {"title":"SQL for Data Analysis","description":"Query databases confidently with SQL.","content":"SELECT, JOIN, aggregations, window functions, CTEs, PostgreSQL and BigQuery.","difficulty":"beginner","required_tier":"free","category":"Data Science"},
    {"title":"Data Visualisation with Tableau","description":"Turn raw data into compelling visual stories.","content":"Interactive dashboards, charts, and reports in Tableau.","difficulty":"intermediate","required_tier":"pro","category":"Data Science"},
    {"title":"Statistics for Data Science","description":"Build a solid statistical foundation for machine learning.","content":"Probability distributions, hypothesis testing, A/B testing, regression analysis.","difficulty":"intermediate","required_tier":"pro","category":"Data Science"},
    {"title":"Apache Spark & Big Data","description":"Process massive datasets with Apache Spark and PySpark.","content":"Distributed computing, RDDs, DataFrames, Spark SQL, and Kafka integration.","difficulty":"advanced","required_tier":"premium","category":"Data Science"},
    # Cloud Computing
    {"title":"AWS Cloud Practitioner","description":"Get started with Amazon Web Services and cloud fundamentals.","content":"EC2, S3, RDS, Lambda, IAM, VPC, and the cloud pricing model.","difficulty":"beginner","required_tier":"free","category":"Cloud Computing"},
    {"title":"AWS Solutions Architect","description":"Design scalable, highly-available architectures on AWS.","content":"VPC design, auto-scaling, load balancing, serverless, databases, SAA-C03 prep.","difficulty":"advanced","required_tier":"premium","category":"Cloud Computing"},
    {"title":"Google Cloud Platform Fundamentals","description":"Explore GCP services and build cloud-native applications.","content":"Compute Engine, Cloud Run, Cloud Functions, BigQuery, and Cloud Storage.","difficulty":"intermediate","required_tier":"pro","category":"Cloud Computing"},
    {"title":"Serverless Architecture","description":"Build event-driven applications without managing servers.","content":"AWS Lambda, API Gateway, DynamoDB, EventBridge, Firebase, Supabase.","difficulty":"intermediate","required_tier":"pro","category":"Cloud Computing"},
    # Backend Development
    {"title":"FastAPI: Modern Python APIs","description":"Build fast, production-ready REST APIs with FastAPI.","content":"Pydantic models, dependency injection, JWT auth, database integration, OpenAPI.","difficulty":"intermediate","required_tier":"pro","category":"Backend Development"},
    {"title":"Node.js & Express Backend","description":"Build scalable server-side applications with Node.js.","content":"REST API design, middleware, authentication, file uploads, WebSockets.","difficulty":"intermediate","required_tier":"pro","category":"Backend Development"},
    {"title":"Database Design & PostgreSQL","description":"Design efficient relational databases and master PostgreSQL.","content":"ER modelling, normalisation, indexes, query optimisation, stored procedures.","difficulty":"intermediate","required_tier":"pro","category":"Backend Development"},
    {"title":"System Design Fundamentals","description":"Learn to design large-scale distributed systems.","content":"Load balancing, caching, message queues, database sharding, CAP theorem.","difficulty":"advanced","required_tier":"premium","category":"Backend Development"},
    {"title":"API Security Best Practices","description":"Secure your APIs against common vulnerabilities.","content":"OAuth2, JWT, API keys, rate limiting, input validation, OWASP Top 10.","difficulty":"advanced","required_tier":"premium","category":"Backend Development"},
]

# attach thumbnails
for c in COURSES:
    c["thumbnail_url"] = THUMBS.get(c["category"], "https://images.unsplash.com/photo-1516116216624-53e697fedbea?w=800&auto=format&fit=crop")

# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------
def get_token() -> str:
    supabase_url = os.getenv("NEXT_PUBLIC_SUPABASE_URL", "")
    anon_key     = os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY", "")
    if not supabase_url or not anon_key:
        print("ERROR: Set NEXT_PUBLIC_SUPABASE_URL and NEXT_PUBLIC_SUPABASE_ANON_KEY"); sys.exit(1)
    if not ADMIN_PASSWORD:
        print("ERROR: Set ADMIN_PASSWORD"); sys.exit(1)
    resp = httpx.post(
        f"{supabase_url}/auth/v1/token?grant_type=password",
        headers={"apikey": anon_key, "Content-Type": "application/json"},
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
        timeout=15,
    )
    if resp.status_code != 200:
        print(f"Auth failed: {resp.status_code} {resp.text}"); sys.exit(1)
    return resp.json()["access_token"]


def fetch_existing_courses(token: str) -> dict:
    resp = httpx.get(f"{API_BASE}/courses/?limit=500", headers={"Authorization": f"Bearer {token}"}, timeout=15)
    if not resp.is_success:
        return {}
    return {c["title"]: c["id"] for c in resp.json()}


def get_lesson_count(token: str, course_id: str) -> int:
    """Return how many lessons already exist for a course."""
    resp = httpx.get(
        f"{API_BASE}/lessons/course/{course_id}",
        headers={"Authorization": f"Bearer {token}"},
        timeout=15,
    )
    if resp.is_success:
        return len(resp.json())
    return 0


def seed_lessons(token: str, course_id: str, topic: str):
    lessons = make_lessons(course_id, topic)
    ok = 0
    for lesson in lessons:
        resp = httpx.post(
            f"{API_BASE}/lessons/",
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            json=lesson,
            timeout=15,
        )
        if resp.status_code == 201:
            ok += 1
        else:
            print(f"      \u2717  Lesson '{lesson['title']}' \u2014 {resp.status_code}: {resp.text[:80]}")
    print(f"      \u2192 {ok}/{len(lessons)} lessons seeded")


def seed(token: str):
    existing = fetch_existing_courses(token)
    created = updated = lessons_added = 0

    for course in COURSES:
        if course["title"] in existing:
            course_id = existing[course["title"]]
            resp = httpx.patch(
                f"{API_BASE}/courses/{course_id}",
                headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
                json=course, timeout=15,
            )
            if resp.status_code == 200:
                print(f"  \u21bb  {course['title']} [{course['required_tier'].upper()}]")
                updated += 1
            else:
                print(f"  \u2717  {course['title']} \u2014 {resp.status_code}: {resp.text[:80]}")
                continue
        else:
            resp = httpx.post(
                f"{API_BASE}/courses/",
                headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
                json=course, timeout=15,
            )
            if resp.status_code == 201:
                course_id = resp.json()["id"]
                print(f"  \u2713  {course['title']} [{course['required_tier'].upper()}]")
                created += 1
            else:
                print(f"  \u2717  {course['title']} \u2014 {resp.status_code}: {resp.text[:80]}")
                continue

        # Always ensure lessons exist
        existing_count = get_lesson_count(token, course_id)
        if existing_count == 0:
            print(f"      \u21b3 Seeding 7 lessons...")
            seed_lessons(token, course_id, course["title"])
            lessons_added += 1
        else:
            print(f"      \u21b3 Already has {existing_count} lessons \u2014 skipped")

    print(f"\nDone: {created} created, {updated} updated, {lessons_added} courses got new lessons.")


def seed_plans(token: str):
    """Ensure Pro and Premium plans exist so courses can be linked to them."""
    plans_to_seed = [
        {"name": "Pro", "price": 1000, "currency": "usd", "interval": "month"},
        {"name": "Premium", "price": 2500, "currency": "usd", "interval": "month"}
    ]
    resp = httpx.get(f"{API_BASE}/plans/", headers={"Authorization": f"Bearer {token}"}, timeout=15)
    existing = []
    if resp.is_success:
        existing = [p["name"].lower() for p in resp.json()]

    for plan in plans_to_seed:
        if plan["name"].lower() not in existing:
            r = httpx.post(
                f"{API_BASE}/plans/",
                headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
                json=plan,
                timeout=15
            )
            if r.status_code == 201:
                print(f"Created Plan: {plan['name']}")
            else:
                print(f"Failed to create Plan {plan['name']}: {r.text}")


if __name__ == "__main__":
    # Load .env files
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

    print(f"Seeding {len(COURSES)} courses to {API_BASE}...")
    token = get_token()
    seed_plans(token)
    seed(token)
