"""Tests for app/crypto.py."""

import pytest

from app.crypto import decrypt_card_data, encrypt_card_data


def test_round_trip_returns_original_plaintext():
    plaintext = "4111111111111111"
    ciphertext = encrypt_card_data(plaintext)
    assert decrypt_card_data(ciphertext) == plaintext


def test_ciphertext_does_not_contain_the_plaintext():
    plaintext = "4111111111111111"
    ciphertext = encrypt_card_data(plaintext)
    assert plaintext not in ciphertext


def test_encrypting_same_plaintext_twice_gives_different_ciphertext():
    plaintext = "4111111111111111"
    first = encrypt_card_data(plaintext)
    second = encrypt_card_data(plaintext)
    assert first != second


def test_tampered_ciphertext_is_rejected():
    ciphertext = encrypt_card_data("4111111111111111")
    tampered = ciphertext[:-4] + "AAAA"
    with pytest.raises(ValueError):
        decrypt_card_data(tampered)
