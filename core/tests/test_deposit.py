import uuid
from fastapi.testclient import TestClient

def test_deposit_settled(client):
    # register user
    register = client.post("/register", json={"email": "test@test.com", "password": "password123"})
    assert register.status_code ==200
    assert "id" in register.json()
    assert register.json()["email"]=="test@test.com"
    # login
    response = client.post("/login", data={"username": "test@test.com", "password": "password123"})
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # create account
    account_response = client.post("/accounts", headers=headers, json={"account_type": "user"})
    account_id = account_response.json()["id"]

    # deposit
    key = str(uuid.uuid4())
    deposit_response = client.post("/deposits", headers=headers, json={
        "account_id": account_id,
        "amount": "100.00",
        "idempotency_key": key
    })

    ref_id = deposit_response.json()["reference_id"]


    # simulate bank callback
    callback_response =client.post("/bank/callback", 
        json={"reference_id": ref_id, "status": "settled"},
        headers={"x-webhook-secret": "a8f3d2c1b7e94f6a2d1c8b3e7f9a4d2c"}
    )
    assert callback_response.status_code == 200
    
    balance_response = client.get(f"/accounts/{account_id}/balance", headers=headers)
    assert balance_response.status_code == 200
    assert balance_response.json()["Balance"] == 100.00
