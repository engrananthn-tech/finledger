from pydantic import BaseModel, EmailStr, ConfigDict
from enum import Enum as PyEnum
from uuid import UUID
from decimal import Decimal
from datetime import datetime
class TokenData(BaseModel):
    id: int

class EntityType(PyEnum):
    transaction="transaction"
    ledger="ledger"
    account="account"
    user="user"

class Action(PyEnum):
    created="created"
    failed="failed"
    settled="settled"
    expired="expired"

class ActorType(PyEnum):
    user = "user"
    system = "system"

class AccountType(PyEnum):
    user = "user"
    system = "system"


class TransactionStatus(PyEnum):
    settled = "settled"
    failed = "failed"
    pending = "pending"

class LedgerDirection(PyEnum):
    credit = "credit"
    debit = "debit"

class TransactionType(PyEnum):
    withdrawal = "withdrawal"
    transfer = "transfer"
    deposit ="deposit"

class SystemAccountName(PyEnum):
    platform_cash = "platform_cash"
    platform_revenue = "platform_revenue"

class User(BaseModel):
    email:EmailStr
    password:str

class Account(BaseModel):
    account_type: AccountType
    name: SystemAccountName|None = None


class TransferInput(BaseModel):
    idempotency_key: str
    from_account_id: int|None=None
    to_account_id: int
    amount:int

class DepositInput(BaseModel):
    idempotency_key: str
    amount:int
    account_id: int|None=None

class WithdrawalInput(BaseModel):
    idempotency_key: str
    amount:int
    account_id: int|None=None

class BankCallbackInput(BaseModel):
    reference_id: UUID
    status : TransactionStatus
    secret_key: str

class TransactionsResponse(BaseModel):
    id:int
    from_account_id:int|None=None
    to_account_id:int|None=None
    amount:int
    fee:Decimal
    reference_id: UUID
    type:TransactionType 
    status :TransactionStatus
    created_at: datetime
    updated_at : datetime
    model_config = ConfigDict(from_attributes=True)

class LedgerEntryResponse(BaseModel):
    id: int
    account_id: int | None
    amount: Decimal
    reference_id: UUID
    direction: LedgerDirection
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class BalanceResponse(BaseModel):
    account_id: int
    balance: Decimal
    model_config = ConfigDict(from_attributes=True)

class AccountResponse(BaseModel):
    id: int
    name: SystemAccountName | None
    user_id: int | None
    account_type: AccountType
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class AuditLogResponse(BaseModel):
    id: int
    entity_type: EntityType
    entity_id: int
    action: Action
    actor_type: ActorType
    actor_id: int | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)