import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Load .env before resolving DATABASE_URL; this module is imported before main.py
# finishes importing the application routers.
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./desifit.db")

# For SQLite, check_same_thread=False allows multi-threaded access in FastAPI/Streamlit
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {},
    echo=False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
