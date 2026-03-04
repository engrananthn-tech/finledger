import uuid
from fastapi.testclient import TestClient
from tests.conftest import create_funded_account

def test_withdrawal_settled(client):
    headers, account_id = create_funded_account(client)

    key = str(uuid.uuid4())
    withdrawal_response = client.post("/withdrawals", headers=headers, json={
    "account_id": account_id,
    "amount": "100.00",
    "idempotency_key": key
    })
    assert withdrawal_response.status_code == 200
    ref_id = withdrawal_response.json()["reference_id"]

    callback_response =client.post("/bank/callback", 
        json={"reference_id": ref_id, "status": "settled"},
        headers={"x-webhook-secret": "a8f3d2c1b7e94f6a2d1c8b3e7f9a4d2c"}
    )
    assert callback_response.status_code == 200

    balance_response = client.get(f"/accounts/{account_id}/balance", headers=headers)
    assert balance_response.status_code == 200
    assert balance_response.json()["Balance"] == 0   