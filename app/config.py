"""Centralized application configuration.

Values here are read once at import time. Keeping configuration in one
place means nothing else in the codebase hardcodes paths or settings
directly.
"""

import os

from dotenv import load_dotenv

load_dotenv()

DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./tokenizer.db")
