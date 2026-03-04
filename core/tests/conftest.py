import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from main import app, seed_system_accounts
from database import get_db, Base
import models
import main
import uuid
TEST_DATABASE_URL = "postgresql://postgres:password@localhost/finance_test"

engine = create_engine(TEST_DATABASE_URL)
TestingSessionLocal = sessionmaker(bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
        db.commit()
    except:
        db.rollback()
        raise
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture()
def client():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    seed_system_accounts(db)
    db.commit()
    db.close()
    yield TestClient(app)
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def db():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

def create_funded_account(client, email= "test@test.com", password= "password123", amount =100):
    client.post("/register", json={"email": email, "password": password})

    response = client.post("/login", data={"username": email, "password": password})
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    account_response = client.post("/accounts", headers=headers, json={"account_type": "user"})
    account_id = account_response.json()["id"]

    key = str(uuid.uuid4())
    deposit_response = client.post("/deposits", headers=headers, json={
        "account_id": account_id,
        "amount": amount,
        "idempotency_key": key
    })
    ref_id =deposit_response.json()["reference_id"]

    client.post("/bank/callback", 
    json={"reference_id": ref_id, "status": "settled"},
    headers={"x-webhook-secret": "a8f3d2c1b7e94f6a2d1c8b3e7f9a4d2c"}
    )

    return headers, account_id