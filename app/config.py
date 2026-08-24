"""Centralized application configuration.

Values here are read once at import time. Keeping configuration in one
place means nothing else in the codebase hardcodes paths or settings
directly.
"""

import os

from dotenv import load_dotenv

load_dotenv()

DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./tokenizer.db")

FERNET_KEY: str | None = os.getenv("FERNET_KEY")
if not FERNET_KEY:
    raise RuntimeError(
        "FERNET_KEY is not set. Generate one with "
        "`python -c \"from cryptography.fernet import Fernet; "
        "print(Fernet.generate_key().decode())\"` and add it to .env."
    )

API_KEY: str | None = os.getenv("API_KEY")
if not API_KEY:
    raise RuntimeError(
        "API_KEY is not set. Generate one with "
        "`python -c \"import secrets; print(secrets.token_urlsafe(32))\"` "
        "and add it to .env."
    )
