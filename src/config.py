import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).parent.parent

DATA_DIR = BASE_DIR / "data"    
DATA_DIR.mkdir(exist_ok=True)

DB_NAME = os.getenv("DB_NAME", "default.db")
DB_PATH = DATA_DIR / DB_NAME
DATABASE_URL = f"sqlite:///{DB_PATH}"

MODEL_DIR = os.getenv("MODEL_DIR", None)