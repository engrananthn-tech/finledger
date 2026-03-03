from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import schemas, utils, models
from sqlalchemy.exc import IntegrityError
import uuid
import httpx
from oauth2 import get_regular_user
from sqlalchemy import func
from database import get_db
from decimal import Decimal
from config import settings
router = APIRouter(prefix="/withdrawals", tags=['Withdrawals'])

@router.post("/")
async def deposit(input: schemas.WithdrawalInput, db: Session = Depends(get_db), current_user: dict = Depends(get_regular_user)):
    try:
        if input.account_id is None:
            accounts = db.query(models.Account).filter(models.Account.user_id == current_user.id).all()
            if not accounts:
                raise HTTPException(404, "Account not found")
            if len(accounts) > 1:
                raise HTTPException(400, "to_account_id required")
            account_id = accounts[0].id
        else:
            account_id = input.account_id
        balance = db.query(func.sum(models.LedgerEntry.amount)).filter(models.LedgerEntry.account_id == account_id).scalar()
        if not balance or int(balance) < int(input.amount):
            raise HTTPException(409, "Insufficient balance")
        reference_id = uuid.uuid4()
        try:
            idempotency = models.IdempotencyKeys(idempotency_key=input.idempotency_key, reference_id=reference_id)
            db.add(idempotency)
            db.flush()
        except IntegrityError:
            db.rollback() 
            reference = db.query(models.IdempotencyKeys).filter(
                models.IdempotencyKeys.idempotency_key == input.idempotency_key
            ).first()
            return reference.reference_id
    
        fee = Decimal('0.001') * input.amount
        fee = min(fee, Decimal('2.00'))
        fee = fee.quantize(Decimal('0.01'))

        new_transaction = models.Transaction(from_account_id=account_id, amount=input.amount, status=schemas.TransactionStatus.pending, reference_id=reference_id, type= schemas.TransactionType.withdrawal, fee=fee)

        db.add(new_transaction)
        db.flush()
        audit = models.AuditLog(entity_type=schemas.EntityType.transaction, entity_id = new_transaction.id, action =schemas.Action.created, actor_type= schemas.ActorType.user, actor_id = current_user.id)
        db.add(audit)
        db.commit() 

    except HTTPException:
        db.rollback()
        raise
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="An error occurred")
    amount = input.amount-fee
    try:
        async with httpx.AsyncClient() as client:
            await client.post(
                "https://finledger-stmj.onrender.com/bank/deposits",
                json={"reference_id": str(reference_id), "amount": str(amount), "secret_key": settings.secret_key}
            )
    except Exception:
        pass
        


