"""Token generation and the create/retrieve operations built on it.

This is the orchestration layer between the database (models.py) and
encryption (crypto.py): it decides what a "tokenize" or "detokenize"
operation actually does, so that route handlers stay thin and only
deal with HTTP concerns.
"""

import json
import secrets

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.crypto import decrypt_card_data, encrypt_card_data
from app.models import CardToken
from app.schemas import CardCreateRequest


def generate_token() -> str:
    """Generate a cryptographically random, unguessable token.

    128 bits of entropy from `secrets` (not `random`, which is
    predictable and unsuitable for anything security-sensitive).
    """
    return "tok_" + secrets.token_hex(16)


def create_card_token(db: Session, card: CardCreateRequest) -> CardToken:
    """Encrypt the given card data and persist it under a new token.

    Retries once with a fresh token on the near-impossible chance of a
    token collision, instead of letting the request fail outright.
    """
    payload = json.dumps(
        {
            "card_number": card.card_number,
            "expiration_month": card.expiration_month,
            "expiration_year": card.expiration_year,
            "cvv": card.cvv,
        }
    )
    ciphertext = encrypt_card_data(payload)
    record = CardToken(token=generate_token(), encrypted_card_data=ciphertext)

    db.add(record)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        record.token = generate_token()
        db.add(record)
        db.commit()

    db.refresh(record)
    return record


def get_decrypted_card_data(db: Session, token: str) -> dict | None:
    """Look up a token and return its decrypted card data, or None if not found."""
    record = db.query(CardToken).filter_by(token=token).first()
    if record is None:
        return None
    plaintext_json = decrypt_card_data(record.encrypted_card_data)
    return json.loads(plaintext_json)
