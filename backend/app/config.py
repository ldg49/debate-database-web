import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "")
DATABASE_READONLY_URL = os.getenv("DATABASE_READONLY_URL", "") or DATABASE_URL

CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
