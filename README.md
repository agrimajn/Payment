# Secure Credit Card Tokenization Service

A backend REST API that accepts credit card data, validates it, encrypts it,
and issues a random token that stands in for it — so callers never need to
store or transmit the real card number after the initial request.

Built with **FastAPI**, **SQLAlchemy**, **SQLite**, **Pydantic**, and the
`cryptography` library's **Fernet** implementation.

> This is a portfolio project demonstrating backend engineering and secure
> coding practices. It is **not** PCI-DSS compliant and is not intended for
> production payment processing.

For the full design rationale — why tokenization exists, encryption vs.
hashing, request flow diagrams, and per-component reasoning — see
[ARCHITECTURE.md](ARCHITECTURE.md).

## Features

- Card data validation: digit format, length, Luhn checksum, expiration, CVV
- Authenticated symmetric encryption (Fernet) for all stored card data —
  plaintext is never written to disk
- Cryptographically random tokens (128 bits of entropy via `secrets`) with
  zero mathematical relationship to the underlying card number
- API key authentication with constant-time comparison
- Custom error handling so invalid card numbers are never echoed back in a
  validation error response
- 24 automated tests covering encryption, tokenization, validation, and the
  live API, each run against an isolated in-memory database

## Getting started

### Prerequisites

- Python 3.12+

### Setup

```bash
# Clone and enter the project
git clone https://github.com/agrimajn/Payment.git
cd Payment

# Confirm python3 resolves to 3.12+ before creating the venv --
# on some systems the default python3 is older (e.g. macOS ships 3.9).
# If so, use a specific interpreter instead, e.g. python3.13.
python3 --version

# Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure secrets
cp .env.example .env
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
python -c "import secrets; print(secrets.token_urlsafe(32))"
# paste the two generated values into .env as FERNET_KEY and API_KEY
```

### Run the server

```bash
uvicorn app.main:app --reload
```

The API is now available at `http://127.0.0.1:8000`, with interactive docs
at `http://127.0.0.1:8000/docs`.

### Run the tests

```bash
pytest
```

## API reference

All requests/responses are JSON. `/tokenize` and `/detokenize` require an
`X-API-Key` header; `/health` does not.

### `GET /health`

Liveness check, unauthenticated.

```bash
curl http://127.0.0.1:8000/health
```

```json
{"status": "ok"}
```

### `POST /tokenize`

Validates and encrypts card data, returning a token that references it.

```bash
curl -X POST http://127.0.0.1:8000/tokenize \
  -H "Content-Type: application/json" \
  -H "X-API-Key: <your API key>" \
  -d '{
        "card_number": "4111111111111111",
        "expiration_month": 12,
        "expiration_year": 2030,
        "cvv": "123"
      }'
```

```json
{"token": "tok_4984eae77de80f48320e637ddafb8282", "created_at": "2026-08-24T03:34:05.428836"}
```

Returns `201` on success, `422` on invalid card data, `401` on a missing or
invalid API key.

### `POST /detokenize`

Looks up a token and returns the decrypted card data.

```bash
curl -X POST http://127.0.0.1:8000/detokenize \
  -H "Content-Type: application/json" \
  -H "X-API-Key: <your API key>" \
  -d '{"token": "tok_4984eae77de80f48320e637ddafb8282"}'
```

```json
{"card_number": "4111111111111111", "expiration_month": 12, "expiration_year": 2030, "cvv": "123"}
```

Returns `200` on success, `404` for an unknown token, `401` on a missing or
invalid API key.

## Project structure

```
app/
  main.py          FastAPI app instance, route registration, error handling
  routes.py        Endpoint definitions (/tokenize, /detokenize, /health)
  schemas.py       Pydantic request/response models and validation rules
  models.py        SQLAlchemy ORM models
  database.py      Engine, session factory, and the get_db dependency
  crypto.py        Fernet encryption/decryption
  token_service.py Token generation and create/retrieve orchestration
  auth.py          API key verification
  config.py        Centralized environment configuration
tests/             pytest suite (mirrors the app/ modules above)
ARCHITECTURE.md     Full design rationale and diagrams
```

## Security design highlights

- Card data is validated (including a Luhn checksum) before anything else
  happens to it.
- Card data is encrypted, not hashed — it needs to be recoverable, which is
  exactly the distinction hashing can't provide.
- Fernet encryption is authenticated: tampering with stored ciphertext is
  detected rather than silently producing corrupted output.
- Tokens carry zero information about the card they reference and are
  generated with `secrets`, not `random`.
- The encryption key and API key live only in environment variables,
  never in the database or source code.
- API key comparison uses `secrets.compare_digest` to avoid timing-based
  guessing attacks.
- A custom validation error handler prevents invalid card numbers from
  being reflected back in HTTP error responses.

## Possible future improvements

Explicitly out of scope for this project, but worth naming as the natural
next steps toward a more production-grade system:

- PostgreSQL instead of SQLite, for concurrent write support
- A managed key management service (e.g. AWS KMS) instead of a static
  environment variable key
- Per-client API keys and rate limiting, instead of one shared key
- Structured audit logging of tokenize/detokenize access
- Containerization and a CI pipeline
