"""Pydantic schemas defining what data may cross the API boundary.

Request schemas describe what a client is allowed to send us. Response
schemas describe what we're allowed to send back -- these are kept
separate so that, for example, a tokenize response can never
accidentally include a raw card number.
"""

from datetime import date, datetime

from pydantic import BaseModel, Field, field_validator, model_validator


def _passes_luhn_checksum(card_number: str) -> bool:
    """Standard Luhn algorithm check, the same validity check real card forms run."""
    digits = [int(d) for d in card_number]
    parity = len(digits) % 2
    checksum = 0
    for i, digit in enumerate(digits):
        if i % 2 == parity:
            digit *= 2
            if digit > 9:
                digit -= 9
        checksum += digit
    return checksum % 10 == 0


class CardCreateRequest(BaseModel):
    """Incoming payload for POST /tokenize."""

    card_number: str = Field(..., description="13-19 digit card number, digits only")
    expiration_month: int = Field(..., ge=1, le=12)
    expiration_year: int = Field(..., ge=2024, le=2100)
    cvv: str = Field(..., min_length=3, max_length=4)

    @field_validator("card_number")
    @classmethod
    def validate_card_number(cls, value: str) -> str:
        if not value.isdigit():
            raise ValueError("Card number must contain only digits")
        if not (13 <= len(value) <= 19):
            raise ValueError("Card number must be between 13 and 19 digits")
        if not _passes_luhn_checksum(value):
            raise ValueError("Card number failed checksum validation")
        return value

    @field_validator("cvv")
    @classmethod
    def validate_cvv(cls, value: str) -> str:
        if not value.isdigit():
            raise ValueError("CVV must contain only digits")
        return value

    @model_validator(mode="after")
    def validate_not_expired(self) -> "CardCreateRequest":
        today = date.today()
        if (self.expiration_year, self.expiration_month) < (today.year, today.month):
            raise ValueError("Card expiration date is in the past")
        return self


class TokenResponse(BaseModel):
    """Returned after successfully tokenizing a card."""

    token: str
    created_at: datetime


class CardDataResponse(BaseModel):
    """Returned after a successful, authorized detokenize request."""

    card_number: str
    expiration_month: int
    expiration_year: int
    cvv: str
