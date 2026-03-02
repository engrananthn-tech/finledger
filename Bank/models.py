from database import Base
from sqlalchemy import Column, Integer, String, Enum, Numeric
import schemas
from sqlalchemy.sql.sqltypes import TIMESTAMP
from sqlalchemy.sql.expression import text
import uuid
from sqlalchemy.dialects.postgresql import UUID


class BankTransfer(Base):
    __tablename__="bank_transfers"
    id= Column(Integer, primary_key=True, nullable=False)
    reference_id = Column(UUID(as_uuid=True), default=uuid.uuid4, nullable=False, unique=True)    
    amount=Column(Numeric(precision=10, scale=2), nullable=False)
    direction=Column(Enum(schemas.BankDirection, name="direction_enum"), nullable=False)
    status = Column(Enum(schemas.TransferStatus, name="status_enum"), nullable=False)
    created_at=Column(TIMESTAMP(timezone=True), server_default=text("now()"))