from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import schemas, utils, models
from sqlalchemy.exc import IntegrityError
import uuid
from oauth2 import get_regular_user
from sqlalchemy import func
from main import limiter
from database import get_db
router = APIRouter(prefix="/transfers", tags=['Transfers'])

@limiter.limit("5/minute")
@router.post("/")
def transfer(input: schemas.TransferInput, db: Session= Depends(get_db), current_user: dict = Depends(get_regular_user)):
    if input.from_account_id is None:
        accounts = db.query(models.Account).filter(models.Account.user_id == current_user.id).all()
        if not accounts:
            raise HTTPException(404, "Account not found")
        if len(accounts) > 1:
            raise HTTPException(400, "from_account_id required")
        from_account_id = accounts[0].id
    else:
        from_account_id = input.from_account_id
    if from_account_id == input.to_account_id:
        raise HTTPException(409, detail="Cannot transfer money to same account")
    
    balance = db.query(func.sum(models.LedgerEntry.amount)).filter(models.LedgerEntry.account_id == from_account_id).scalar()
    if not balance or balance < input.amount:
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
    try:
        new_transaction = models.Transaction(from_account_id=from_account_id, to_account_id= input.to_account_id, amount=input.amount, status=schemas.TransactionStatus.settled, reference_id=reference_id, type=schemas.TransactionType.transfer)
        db.add(new_transaction)
        db.flush()
        audit = models.AuditLog(entity_type=schemas.EntityType.transaction, entity_id = new_transaction.id, action =schemas.Action.settled, actor_type= schemas.ActorType.user, actor_id = current_user.id)
        db.add(audit)
        new_debit = models.LedgerEntry(account_id=from_account_id, amount=input.amount, direction = schemas.LedgerDirection.debit, reference_id= reference_id)
        new_credit = models.LedgerEntry(account_id=input.to_account_id, amount=input.amount, direction = schemas.LedgerDirection.credit, reference_id=reference_id)
        db.add(new_credit)
        db.add(new_debit)
        db.flush()
        audit = models.AuditLog(entity_type=schemas.EntityType.ledger, entity_id = new_credit.id, action =schemas.Action.created, actor_type= schemas.ActorType.system)
        db.add(audit)
        db.commit()
    except:
        db.rollback()
        raise HTTPException(status_code=429, detail="An error occured")

    