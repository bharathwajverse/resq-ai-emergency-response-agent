"""
ResQ-AI Standalone Database Seed Runner.
Usage:
    python seed_data.py           # Idempotent seed (skips existing)
    python seed_data.py --reset   # Truncates and reseeds fresh data
    python seed_data.py --force   # Force updates existing data
"""

import sys
import os
import argparse
import logging

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.database import engine, SessionLocal, Base
from app.services.seed_service import seed_initial_data, reset_database

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("seed_runner")


def main():
    parser = argparse.ArgumentParser(description="ResQ-AI Database Seeder")
    parser.add_argument("--reset", action="store_true", help="Reset and re-seed all tables")
    parser.add_argument("--force", action="store_true", help="Force overwrite existing records")
    args = parser.parse_args()

    logger.info("Initializing database tables...")
    import app.models  # noqa: F401
    Base.metadata.create_all(bind=engine)

    with SessionLocal() as db:
        if args.reset:
            logger.info("Resetting database records...")
            counts = reset_database(db)
        else:
            logger.info("Running idempotent seed...")
            counts = seed_initial_data(db, force=args.force)

    logger.info("Seed successful! Summary:")
    for entity, count in counts.items():
        logger.info(f"  - {entity.capitalize()}: {count}")


if __name__ == "__main__":
    main()
