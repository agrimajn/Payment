# Architecture

This document explains the design decisions behind the Secure Credit Card
Tokenization Service: what problem it solves, how the pieces fit together,
and why specific technical choices were made. It is a living document,
updated as the system grows.

## What problem this solves

When a merchant needs to charge a customer again later (subscription
renewals, refunds), it needs a way to reference that customer's card
without storing the card number itself. Storing raw card numbers means
a single database breach exposes every card on file.

**Tokenization** replaces the sensitive value with a random, non-sensitive
placeholder (a "token") that has no mathematical relationship to the
original data. The token is safe to store anywhere. Only this service can
map a token back to the underlying card data, and only for callers who
authenticate as authorized to do so.

```
Merchant's DB                    Tokenization Service
+----------------+               +---------------------------+
| user_id: 42     |              | token: tok_9f8a...         |
| card: tok_9f8a.. |  <--------  | encrypted_card: <ciphertext>|
+----------------+               +---------------------------+
```

## Encryption vs. hashing

These solve different problems and are not interchangeable:

| | Hashing | Encryption |
|---|---|---|
| Direction | One-way | Two-way (reversible with a key) |
| Used for | Verifying a value without ever storing/retrieving the original (e.g. passwords) | Protecting a value while preserving the ability to retrieve the original later |

Card numbers must eventually be retrievable to actually charge the card,
so they are **encrypted** (reversible), not hashed (irreversible). This
service uses `cryptography`'s Fernet implementation for encryption rather
than a custom scheme — rolling your own cryptography is a well-known
anti-pattern; established, audited implementations are used instead.

The encryption key itself is the single point of failure for this scheme:
if it lived in the same place as the ciphertext, a database breach would
expose both the lock and the key. It is kept in an environment variable,
outside version control and outside the database.

## System architecture

```
                     +-------------------------------------------+
                     |           FastAPI Application              |
                     |                                             |
  HTTP Request       |  +-----------+   +---------------------+   |
 -------------------->  |  routes.py |-->|  schemas.py           |  |
  POST /tokenize      |  | (endpoints)|   | (Pydantic validation)|  |
                     |  +-----+-----+   +---------------------+   |
                     |        |                                    |
                     |        v                                    |
                     |  +---------------+   +-----------------+    |
                     |  | crypto.py      |   | token_service.py |  |
                     |  | (encrypt/decrypt)|  | (generate token) |  |
                     |  +-------+-------+   +--------+--------+    |
                     |          |                     |             |
                     |          v                     v             |
                     |       +-----------------------------+        |
                     |       |  models.py + database.py     |       |
                     |       |  (SQLAlchemy ORM -> SQLite)  |        |
                     |       +-----------------------------+        |
                     +-------------------------------------------+
```

Each module has a single responsibility: route handlers don't know how
encryption works, only that something else handles it. This keeps each
piece independently testable and replaceable — e.g. swapping Fernet for
a managed key service later would only touch `crypto.py`.

## Request flows

**Storing a card (tokenize):**

```
Client                     API                        DB
  |  POST /tokenize          |                          |
  |  { card_number, exp,     |                          |
  |    cvv }                  |                          |
  |------------------------->|                          |
  |                           | 1. Validate input        |
  |                           | 2. Encrypt card data      |
  |                           | 3. Generate random token  |
  |                           | 4. Store (token, cipher)  |
  |                           |------------------------->|
  |                           |<-------------------------|
  |  200 { token: "tok_..." }|                          |
  |<-------------------------|                          |
```

**Retrieving a card (detokenize):**

```
Client                     API                        DB
  |  POST /detokenize        |                          |
  |  { token, API key }      |                          |
  |------------------------->|                          |
  |                           | 1. Authenticate caller    |
  |                           | 2. Look up token          |
  |                           |------------------------->|
  |                           |<-------------------------|
  |                           | 3. Decrypt ciphertext     |
  |  200 { card_number, ... }|                          |
  |<-------------------------|                          |
```

Plaintext card data exists only transiently, in memory, during a request.
It is never written to disk unencrypted.

## Current status

- Project scaffolding, dependency management, and environment setup: done.
- FastAPI application entry point: done.
- Database layer (SQLite + SQLAlchemy models, `card_tokens` table): done.
- Input validation (Pydantic schemas, Luhn checksum, expiration and CVV
  checks): done.
- Encryption (Fernet, via crypto.py): done. Verified round-trip
  correctness, non-deterministic ciphertext for identical plaintext,
  and tamper detection on corrupted ciphertext.
- Tokenization (token_service.py: secrets-based token generation,
  create/retrieve orchestration tying validation + encryption +
  storage together): done. Verified full validate -> encrypt ->
  tokenize -> store -> lookup -> decrypt round-trip, plus a 100,000-
  token uniqueness check.
- REST API (routes.py: POST /tokenize, POST /detokenize, GET /health)
  wired to a live server, with a custom validation error handler so
  invalid card numbers are never echoed back in a 422 response body:
  done. Verified live over HTTP -- successful tokenize/detokenize,
  404 on an unknown token, and confirmed no card data leaks into a
  validation error response.
- API key authentication (auth.py: single shared-secret key checked
  via a header, constant-time comparison, protecting /tokenize and
  /detokenize while /health stays open): done. Verified live -- a
  missing key and a wrong key both correctly return 401, a valid key
  succeeds, and /health remains reachable without one.
- Automated tests: not yet implemented.

This section is updated as functionality lands.
