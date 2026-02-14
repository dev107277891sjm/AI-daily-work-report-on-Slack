"""
Create PostgreSQL tables. Run once before first start.
Usage: python -m scripts.init_db
"""
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

database_url = os.getenv("DATABASE_URL")
if not database_url:
    print("ERROR: Set DATABASE_URL in .env")
    sys.exit(1)

from db.session import get_engine, init_db
from db.models import Base

engine = get_engine(database_url)
init_db(engine)
print("Database tables created successfully.")
