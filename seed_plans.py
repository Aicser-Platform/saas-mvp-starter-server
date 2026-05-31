#!/usr/bin/env python3
"""
Seed the plans table with the free / pro / premium tiers.

Names MUST be lowercase: the Stripe webhook matches plan.name against the
checkout tier, and feature_gate.get_user_tier() returns plan.name.lower().

Usage:
    cd saas-mvp-starter-server
    source venv/bin/activate
    python seed_plans.py
"""

from app.db.database import SessionLocal
from app.models.plan import Plan

PLANS = [
    {"name": "free",    "price": 0,    "currency": "usd", "interval": "month"},
    {"name": "pro",     "price": 1999, "currency": "usd", "interval": "month"},
    {"name": "premium", "price": 4999, "currency": "usd", "interval": "month"},
]


def main():
    db = SessionLocal()
    created = updated = 0
    try:
        for cfg in PLANS:
            plan = db.query(Plan).filter(Plan.name == cfg["name"]).first()
            if plan:
                plan.price = cfg["price"]
                plan.currency = cfg["currency"]
                plan.interval = cfg["interval"]
                updated += 1
                print(f"  ↷  {cfg['name']}  [exists, updated]")
            else:
                db.add(Plan(**cfg))
                created += 1
                print(f"  ✓  {cfg['name']}")
        db.commit()
        print(f"\nDone: {created} created, {updated} updated.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
