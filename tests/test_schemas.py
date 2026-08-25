"""Tests for app/schemas.py validation rules."""

import pytest
from pydantic import ValidationError

from app.schemas import CardCreateRequest


def test_valid_card_is_accepted():
    card = CardCreateRequest(
        card_number="4111111111111111", expiration_month=12, expiration_year=2030, cvv="123"
    )
    assert card.card_number == "4111111111111111"


def test_card_number_failing_luhn_checksum_is_rejected():
    with pytest.raises(ValidationError):
        CardCreateRequest(
            card_number="4111111111111112", expiration_month=12, expiration_year=2030, cvv="123"
        )


def test_card_number_with_letters_is_rejected():
    with pytest.raises(ValidationError):
        CardCreateRequest(
            card_number="411111111111111a", expiration_month=12, expiration_year=2030, cvv="123"
        )


def test_expired_card_is_rejected():
    with pytest.raises(ValidationError):
        CardCreateRequest(
            card_number="4111111111111111", expiration_month=1, expiration_year=2020, cvv="123"
        )


def test_non_numeric_cvv_is_rejected():
    with pytest.raises(ValidationError):
        CardCreateRequest(
            card_number="4111111111111111", expiration_month=12, expiration_year=2030, cvv="12a"
        )


def test_cvv_too_short_is_rejected():
    with pytest.raises(ValidationError):
        CardCreateRequest(
            card_number="4111111111111111", expiration_month=12, expiration_year=2030, cvv="12"
        )
