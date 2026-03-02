from enum import Enum as PyEnum
from pydantic import BaseModel
from uuid import UUID
from decimal import Decimal
class BankDirection(PyEnum):
    IN = "IN"
    OUT = "OUT"

class TransferInput(BaseModel):
    reference_id: UUID
    amount: Decimal
    secret_key: str

class TransferStatus(PyEnum):
    settled="settled"
    pending="pending"
    failed="failed"