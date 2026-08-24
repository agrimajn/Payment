"""API key authentication.

A single shared-secret key, checked on protected endpoints. Deliberately
simple -- this models one trusted backend-to-backend integration, not
OAuth-style per-user identity, which this service has no need for.
"""

import secrets

from fastapi import Header, HTTPException, status

from app.config import API_KEY


def verify_api_key(x_api_key: str | None = Header(default=None)) -> None:
    """Raise 401 unless the caller's X-API-Key header matches the real key.

    A missing header and a wrong key both return the same 401 -- a
    missing header isn't a malformed request (422), it's a failed
    authentication attempt. Uses secrets.compare_digest for a
    constant-time comparison, so an attacker can't use response timing
    to infer how many leading characters of a guessed key were correct.
    The `not x_api_key` check short-circuits before compare_digest runs,
    so a missing header never reaches it as None.
    """
    if not x_api_key or not secrets.compare_digest(x_api_key, API_KEY):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")
