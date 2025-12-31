# database.py
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import NullPool

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
# print("DATABASE_URL:", DATABASE_URL)

# Supabase uses a serverless Postgres → use NullPool to avoid stale connections
engine = create_engine(
    DATABASE_URL,
    poolclass=NullPool,     # <-- IMPORTANT for Supabase
    echo=False,
)

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
