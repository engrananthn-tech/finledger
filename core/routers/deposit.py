from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import schemas, utils, models
from sqlalchemy.exc import IntegrityError
import uuid
import httpx
from oauth2 import get_current_user
from database import get_db
from config import settings
import traceback

router = APIRouter(prefix="/deposits")

@router.post("/")
async def deposit(input: schemas.DepositInput, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    
    reference_id = uuid.uuid4()    
    # try:
    if input.account_id is None:
        accounts = db.query(models.Account).filter(models.Account.user_id == current_user.id).all()
        if not accounts:
            raise HTTPException(404, "Account not found")
        if len(accounts) > 1:
            raise HTTPException(400, "to_account_id required")
        account_id = accounts[0].id
    else:
        account_id = input.account_id

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

    new_transaction = models.Transaction(to_account_id=account_id, amount=input.amount, status=schemas.TransactionStatus.pending, reference_id=reference_id, type=schemas.TransactionType.deposit)
    db.add(new_transaction)
    db.flush()
    audit = models.AuditLog(entity_type=schemas.EntityType.transaction, entity_id = new_transaction.id, action =schemas.Action.created, actor_type= schemas.ActorType.user, actor_id = current_user.id)

    db.add(audit)
    db.commit() 

    # except HTTPException:
    #     db.rollback()
    #     raise
    # except Exception as e:
    #     db.rollback()
    #     traceback.print_exc
    #     raise HTTPException(status_code=500, detail="An error occurred")

    # try:
    async with httpx.AsyncClient() as client:
        await client.post(
            "http://127.0.0.1:8000/bank/deposits",
            json={"reference_id": str(reference_id), "amount": input.amount, "secret_key":settings.BANK_WEBHOOK_SECRET}
        )
    # except Exception:
    #     print("HI")
    #     pass



