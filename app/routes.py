"""API route handlers.

Each handler stays intentionally thin: FastAPI + Pydantic handle
request validation automatically, and the real work is delegated to
token_service.py. Handlers here only deal with HTTP concerns --
choosing status codes and translating results into responses.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import (
    CardCreateRequest,
    CardDataResponse,
    DetokenizeRequest,
    TokenResponse,
)
from app.token_service import create_card_token, get_decrypted_card_data

router = APIRouter()


@router.get("/health")
def health_check() -> dict[str, str]:
    """Liveness check. Deliberately unauthenticated -- monitoring and
    load balancers need to reach this without credentials."""
    return {"status": "ok"}


@router.post("/tokenize", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def tokenize_card(card: CardCreateRequest, db: Session = Depends(get_db)) -> TokenResponse:
    """Validate, encrypt, and store card data, returning a token that references it."""
    record = create_card_token(db, card)
    return TokenResponse(token=record.token, created_at=record.created_at)


@router.post("/detokenize", response_model=CardDataResponse)
def detokenize_card(
    request: DetokenizeRequest, db: Session = Depends(get_db)
) -> CardDataResponse:
    """Look up a token and return its decrypted card data."""
    data = get_decrypted_card_data(db, request.token)
    if data is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Token not found")
    return CardDataResponse(**data)
