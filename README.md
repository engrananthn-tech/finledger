# Finance Ledger

Payment backend that handles deposits, withdrawals, and internal transfers. Uses an append-only ledger to track all money movements, handles bank callbacks asynchronously, logs every action for audit, and automatically marks stuck transactions as failed.

---

## What This Is

Two services working together:

- core: the main payment backend (FastAPI + PostgreSQL)
- bank: a fake external bank that processes requests asynchronously and calls back with results

The bank is intentionally unreliable. It introduces delays and random failures to simulate real-world conditions.

---

## How Money Works Here

Balances are never stored. You get a balance by summing ledger entries for an account. If there is no settled ledger entry, there is no balance.

Every transaction creates two ledger entries: one debit and one credit. They net to zero. At any point, the sum of all ledger entries across all accounts equals zero.

The ledger is append-only. Rows are never updated or deleted.

---

## Project Structure

```
finledger/
  core/         main payment backend
  bank/         fake async bank service
```

---

## Setup

Requirements: Python 3.12+, PostgreSQL

Clone the repo:

```
git clone https://github.com/yourusername/finledger.git
cd finledger
```

Set up core:

```
cd core
pip install -r requirements.txt
```

Create a .env file in core/:

```
DATABASE_URL=postgresql://user:password@localhost/finledger_core
SECRET_KEY=your_jwt_secret
BANK_WEBHOOK_SECRET=your_shared_secret
BANK_URL=http://localhost:8001
```

Run migrations:

```
alembic upgrade head
```

Start the server:

```
uvicorn main:app --reload --port 8000
```

Set up bank:

```
cd ../bank
pip install -r requirements.txt
```

Create a .env file in bank/:

```
DATABASE_URL=postgresql://user:password@localhost/finledger_bank
WEBHOOK_SECRET=your_shared_secret
CALLBACK_URL=http://localhost:8000/callback
```

Start the bank:

```
uvicorn main:app --reload --port 8001
```

---

## API Reference

All endpoints except register and login require a Bearer token in the Authorization header.

### Auth

POST /register
Create a new user account.

```
{
  "email": "user@example.com",
  "password": "yourpassword"
}
```

POST /login
Returns a JWT token.

```
{
  "username": "user@example.com",
  "password": "yourpassword"
}
```

### Accounts

POST /accounts
Create a new wallet account for the logged-in user.

GET /accounts/{account_id}/balance
Returns the derived balance for that account. Calculated as sum of settled ledger entries.

### Transactions

POST /deposit
Initiates a deposit from the external bank. Creates a pending transaction. The bank processes it asynchronously and calls back.

```
{
  "account_id": 1,
  "amount": "100.00",
  "idempotency_key": "uuid-here"
}
```

POST /withdraw
Initiates a withdrawal to the external bank. A 0.1% fee applies, capped at 2.00.

```
{
  "account_id": 1,
  "amount": "100.00",
  "idempotency_key": "uuid-here"
}
```

POST /transfer
Transfers money between two internal accounts. Instant. No bank involved.

```
{
  "from_account_id": 1,
  "to_account_id": 2,
  "amount": "50.00",
  "idempotency_key": "uuid-here"
}
```

### Callback (Bank Only)

POST /callback
Called by the bank to settle or fail a transaction. Requires the shared webhook secret in the x-webhook-secret header. Any other caller gets a 401.

---

## How Idempotency Works

Every request includes a reference_id (UUID). If the same reference_id is sent twice, the second request returns the same result as the first and does nothing. This makes retries safe.

The callback endpoint also checks transaction state before processing. If a transaction is already settled or failed, the callback is ignored.

---

## How Failure Recovery Works

A background job runs every 10 minutes. It finds transactions that have been pending for more than 10 minutes and marks them as failed. This handles cases where the bank never calls back.

---

## Audit Logging

Every meaningful event writes a row to the audit log:

- account created
- Transaction created
- Callback received (settled or failed)
- Ledger entries written
- Transaction expired by background job
- Unauthorized callback attempt

Each row records what happened, to which entity, who triggered it (user or system), and when.

---

## Fee Structure

- Deposits: free
- Withdrawals: 0.1% of amount, capped at 2.00
- Internal transfers: free

The fee is recorded as a separate ledger entry crediting the platform revenue account.

---

## Account Types

- user: belongs to a registered user
- system: platform cash and revenue accounts
- escrow: reserved for future use
- external: reserved for future use

---

## What Could Be Added

- Escrow flow for marketplace payments
- Admin endpoints to view all transactions and audit logs
- Rate limiting on transaction endpoints
- Webhook retry logic for failed bank requests
- Multi-currency support
- Transaction history with pagination
- Email notifications on settlement or failure
- Postman collection for testing all flows

---

