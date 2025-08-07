from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine
import os

DATABASE_URL = os.getenv("DATABASE_URL") or "postgresql://user:pass@localhost:5432/mydb"
engine = create_engine(DATABASE_URL)
