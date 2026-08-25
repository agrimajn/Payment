"""Tests for app/token_service.py."""

from app.models import CardToken
from app.schemas import CardCreateRequest
from app.token_service import create_card_token, generate_token, get_decrypted_card_data


def test_generate_token_has_expected_format():
    token = generate_token()
    assert token.startswith("tok_")
    assert len(token) == len("tok_") + 32  # 16 random bytes, hex-encoded


def test_generate_token_is_unique_across_many_calls():
    tokens = {generate_token() for _ in range(10_000)}
    assert len(tokens) == 10_000


def test_create_card_token_stores_ciphertext_not_plaintext(db_session):
    card = CardCreateRequest(
        card_number="4111111111111111", expiration_month=12, expiration_year=2030, cvv="123"
    )
    record = create_card_token(db_session, card)

    assert record.token.startswith("tok_")
    assert "4111111111111111" not in record.encrypted_card_data

    stored = db_session.query(CardToken).filter_by(token=record.token).first()
    assert stored is not None
    assert "4111111111111111" not in stored.encrypted_card_data


def test_get_decrypted_card_data_round_trip(db_session):
    card = CardCreateRequest(
        card_number="4111111111111111", expiration_month=12, expiration_year=2030, cvv="123"
    )
    record = create_card_token(db_session, card)

    data = get_decrypted_card_data(db_session, record.token)

    assert data == card.model_dump()


def test_get_decrypted_card_data_returns_none_for_unknown_token(db_session):
    assert get_decrypted_card_data(db_session, "tok_doesnotexist") is None
