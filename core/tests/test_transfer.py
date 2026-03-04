import uuid
from fastapi.testclient import TestClient
from tests.conftest import create_funded_account

def test_internal_transfer(client):
    headers_a, account_a = create_funded_account(client, email="user_a@test.com")
    headers_b, account_b = create_funded_account(client, email="user_b@test.com")

    key = str(uuid.uuid4())
    response = client.post("/transfers", headers=headers_a, json={
        "from_account_id": account_a,
        "to_account_id": account_b,
        "amount": "50.00",
        "idempotency_key": key
    })
    assert response.status_code == 200

    balance_a = client.get(f"/accounts/{account_a}/balance", headers=headers_a)
    balance_b = client.get(f"/accounts/{account_b}/balance", headers=headers_b)

    assert balance_a.json()["Balance"] == 50.0
    assert balance_b.json()["Balance"] == 150.0