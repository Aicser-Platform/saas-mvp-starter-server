#!/usr/bin/env python3
"""
Remove duplicate plan rows that have capitalised names (Pro, Premium) and
re-point any subscriptions that reference them to the canonical lowercase plans.

Usage:
    cd saas-mvp-starter-server
    source venv/bin/activate
    python cleanup_plans.py
"""

from app.db.database import SessionLocal
from app.models.plan import Plan
from app.models.subscription import Subscription
from app.models.course import Course


def main():
    db = SessionLocal()
    try:
        all_plans = db.query(Plan).all()
        print("Current plans in DB:")
        for p in all_plans:
            print(f"  {p.id}  name={p.name!r}  price={p.price}")

        # Build a map: lowercased name → list of plans (sorted oldest first)
        by_name: dict[str, list[Plan]] = {}
        for p in all_plans:
            key = p.name.lower()
            by_name.setdefault(key, []).append(p)

        for canonical_name, plans in by_name.items():
            if len(plans) <= 1:
                continue  # no duplicate

            # Prefer the plan whose name is already lowercase (canonical)
            canonical = next((p for p in plans if p.name == canonical_name), plans[0])
            duplicates = [p for p in plans if p.id != canonical.id]

            print(f"\n  '{canonical_name}': canonical id={canonical.id}")
            for dup in duplicates:
                print(f"    dup  id={dup.id}  name={dup.name!r}  → re-pointing subscriptions…")
                sub_count = (
                    db.query(Subscription)
                    .filter(Subscription.plan_id == dup.id)
                    .update({"plan_id": canonical.id})
                )
                print(f"      updated {sub_count} subscription(s)")
                course_count = (
                    db.query(Course)
                    .filter(Course.required_plan_id == dup.id)
                    .update({"required_plan_id": canonical.id})
                )
                print(f"      updated {course_count} course(s)")
                db.flush()
                db.delete(dup)
                print(f"      deleted plan {dup.id!r}")

        db.commit()
        print("\nDone. Remaining plans:")
        for p in db.query(Plan).all():
            print(f"  {p.id}  name={p.name!r}  price={p.price}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
