"""Central settings for FinGuard, loaded from environment variables / .env."""

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DB_PATH = PROJECT_ROOT / os.getenv("FINGUARD_DB_PATH" , "data/finguard.db")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
