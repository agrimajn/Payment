"""End-to-end tests for the REST API endpoints, via FastAPI's TestClient."""


def test_health_check_requires_no_auth(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_tokenize_without_api_key_is_rejected(client, valid_card_payload):
    response = client.post("/tokenize", json=valid_card_payload)
    assert response.status_code == 401


def test_tokenize_with_wrong_api_key_is_rejected(client, valid_card_payload):
    response = client.post(
        "/tokenize", json=valid_card_payload, headers={"X-API-Key": "wrong-key"}
    )
    assert response.status_code == 401


def test_tokenize_with_valid_key_returns_token(client, valid_card_payload, auth_headers):
    response = client.post("/tokenize", json=valid_card_payload, headers=auth_headers)
    assert response.status_code == 201
    body = response.json()
    assert body["token"].startswith("tok_")
    assert "card_number" not in body


def test_tokenize_response_never_contains_the_submitted_card_number(
    client, valid_card_payload, auth_headers
):
    response = client.post("/tokenize", json=valid_card_payload, headers=auth_headers)
    assert valid_card_payload["card_number"] not in response.text


def test_tokenize_invalid_card_returns_422_without_echoing_input(client, auth_headers):
    bad_payload = {
        "card_number": "4111111111111112",
        "expiration_month": 12,
        "expiration_year": 2030,
        "cvv": "123",
    }
    response = client.post("/tokenize", json=bad_payload, headers=auth_headers)
    assert response.status_code == 422
    assert "4111111111111112" not in response.text


def test_full_tokenize_then_detokenize_round_trip(client, valid_card_payload, auth_headers):
    tokenize_response = client.post("/tokenize", json=valid_card_payload, headers=auth_headers)
    token = tokenize_response.json()["token"]

    detokenize_response = client.post(
        "/detokenize", json={"token": token}, headers=auth_headers
    )

    assert detokenize_response.status_code == 200
    assert detokenize_response.json() == valid_card_payload


def test_detokenize_without_api_key_is_rejected(client, auth_headers, valid_card_payload):
    tokenize_response = client.post("/tokenize", json=valid_card_payload, headers=auth_headers)
    token = tokenize_response.json()["token"]

    response = client.post("/detokenize", json={"token": token})
    assert response.status_code == 401


def test_detokenize_unknown_token_returns_404(client, auth_headers):
    response = client.post("/detokenize", json={"token": "tok_doesnotexist"}, headers=auth_headers)
    assert response.status_code == 404
