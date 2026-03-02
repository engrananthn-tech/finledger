from database import Base
from sqlalchemy import Column, Integer, String, ForeignKey, Enum, Index, UniqueConstraint, Numeric
from sqlalchemy.sql.sqltypes import TIMESTAMP
from sqlalchemy.sql.expression import text 
from schemas import AccountType, TransactionStatus, LedgerDirection, TransactionType, EntityType, Action, ActorType, SystemAccountName
from sqlalchemy.dialects.postgresql import UUID


class User(Base):
    __tablename__="users"
    id=Column(Integer, primary_key=True)
    email=Column(String, nullable=False, unique=True)
    password=Column(String, nullable=False)
    created_at = Column(TIMESTAMP(timezone = True), server_default= text('now()'))

class Account(Base):
    __tablename__="accounts"
    id=Column(Integer, primary_key=True)
    name = Column(Enum(SystemAccountName, name ="system_account_name"), nullable=True)
    user_id=Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    account_type=Column(Enum(AccountType, name="account_type"), nullable=False)
    created_at = Column(TIMESTAMP(timezone = True), server_default= text('now()'))
    __table_args__=(
        Index(
            "idx_accounts_user_id_",
            "user_id",
        ),
    )

class LedgerEntry(Base):
    __tablename__ = "ledger_entries"
    id=Column(Integer, primary_key=True)
    account_id =Column(Integer, ForeignKey("accounts.id", ondelete="SET NULL"), nullable=True)
    amount= Column(Numeric(precision=10, scale=2), nullable=False)
    reference_id = Column(UUID(as_uuid=True), nullable=False)
    direction= Column(Enum(LedgerDirection, name="ledger_direction"), nullable=False)
    created_at = Column(TIMESTAMP(timezone = True), server_default= text('now()'))
    __table_args__ = (
        UniqueConstraint('reference_id', 'direction', name='uq_ledger_reference_direction'),
    )
    __table_args__ = (
        Index(
            "idx_ledgerentries_account_status",
            "account_id","direction"
        ),
    )

class Transaction(Base):
    __tablename__ = "transaction"
    id=Column(Integer, primary_key=True)
    from_account_id =Column(Integer, ForeignKey("accounts.id", ondelete="SET NULL"), nullable=True)
    to_account_id =Column(Integer, ForeignKey("accounts.id", ondelete="SET NULL"), nullable=True)
    amount= Column(Integer, nullable=False)
    fee= Column(Numeric(precision=10, scale=2), nullable=True, default=0)
    reference_id = Column(UUID(as_uuid=True), nullable=False)
    type= Column(Enum(TransactionType, name="transaction_type"), nullable=False)
    status = Column(Enum(TransactionStatus, name = "transaction_status", nullable=False))
    created_at = Column(TIMESTAMP(timezone = True), server_default= text('now()'))
    updated_at = Column(TIMESTAMP(timezone = True), server_default= text('now()'))

class IdempotencyKeys(Base):
    __tablename__="idempotency_keys"
    id = Column(Integer, primary_key=True)
    idempotency_key= Column(String, unique=True, nullable=False)
    reference_id = Column(UUID(as_uuid=True), nullable=False)
    created_at = Column(TIMESTAMP(timezone = True), server_default= text('now()'))

class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(Integer, primary_key=True)
    entity_type = Column(Enum(EntityType, name="entity_type"), nullable=False)
    entity_id = Column(Integer, nullable=False)
    action= Column(Enum(Action, name = "action"), nullable=False)
    actor_type= Column(Enum(ActorType, name = "actor_type"), nullable=False)
    actor_id = Column(Integer, ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    created_at = Column(TIMESTAMP(timezone = True), server_default= text('now()'))


# 1️⃣ Python import
# import uuid

# Generate:

# ref_id = uuid.uuid4()
# 2️⃣ SQLAlchemy model import
# from sqlalchemy import Column
# from sqlalchemy.dialects.postgresql import UUID

# Column:

# reference_id = Column(UUID(as_uuid=True), nullable=False)
# 3️⃣ Pydantic schema import
# from uuid import UUID

# Schema field:

# reference_id: UUID