"""Encryption and decryption of sensitive card data.

Wraps the `cryptography` library's Fernet implementation. Nothing here
implements cryptographic primitives directly -- Fernet handles AES
encryption, authentication (tamper detection), and key rotation safety
internally. This module's only job is to give the rest of the app a
simple encrypt/decrypt interface and keep the key handling in one place.
"""

from cryptography.fernet import Fernet, InvalidToken

from app.config import FERNET_KEY

_fernet = Fernet(FERNET_KEY.encode())


def encrypt_card_data(plaintext: str) -> str:
    """Encrypt a plaintext string, returning ciphertext safe to store."""
    return _fernet.encrypt(plaintext.encode()).decode()


def decrypt_card_data(ciphertext: str) -> str:
    """Decrypt ciphertext produced by encrypt_card_data.

    Raises InvalidToken if the ciphertext was tampered with, corrupted,
    or encrypted under a different key.
    """
    try:
        return _fernet.decrypt(ciphertext.encode()).decode()
    except InvalidToken:
        raise ValueError("Card data could not be decrypted: invalid or tampered ciphertext")
