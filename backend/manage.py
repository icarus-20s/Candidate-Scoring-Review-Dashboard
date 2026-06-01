"""
Management script for TechKraft backend.

Usage:
    python manage.py reseed     # Delete DB and reseed sample data
"""

import sys
import os
import asyncio

sys.path.insert(0, os.path.dirname(__file__))

async def reseed():
    db_path = os.path.join(os.path.dirname(__file__), "app.db")
    if os.path.exists(db_path):
        os.remove(db_path)
        print("Deleted app.db")
    else:
        print("No app.db found")

    from app.models import init_db
    from app.services.candidate_service import seed_admin, seed_sample_candidates

    await init_db()
    await seed_admin()
    await seed_sample_candidates()
    print("Database recreated with fresh seed data (30 candidates + admin user)")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python manage.py <command>")
        print("Commands: reseed")
        sys.exit(1)

    cmd = sys.argv[1]
    if cmd == "reseed":
        asyncio.run(reseed())
    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)
