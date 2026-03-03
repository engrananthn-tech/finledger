from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import schemas, utils, models
from sqlalchemy.exc import IntegrityError
from oauth2 import get_regular_user
from database import get_db
from sqlalchemy import func, case, or_
from typing import List
router = APIRouter(prefix="/accounts")

@router.post("/", response_model= schemas.AccountResponse)
def create_account(payload: schemas.Account, db: Session= Depends(get_db), current_user :dict =Depends(get_regular_user)):
    print("hello")
    new = models.Account(user_id = current_user.id, account_type = payload.account_type)
    db.add(new)
    db.flush()
    audit = models.AuditLog(entity_type=schemas.EntityType.account, entity_id = new.id, action =schemas.Action.created, actor_type= schemas.ActorType.user, actor_id = current_user.id)
    db.add(audit)
    db.commit()
    db.refresh(new)
    return new

@router.get("/{id}/balance")
def check_balance(id:int = id, db: Session= Depends(get_db), current_user :dict =Depends(get_regular_user)):
    account = db.query(models.Account).filter(models.Account.user_id== current_user.id).filter(models.Account.id == id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    balance=  db.query(func.coalesce(func.sum(case((models.LedgerEntry.direction == schemas.LedgerDirection.credit, models.LedgerEntry.amount),(models.LedgerEntry.direction == schemas.LedgerDirection.debit, -models.LedgerEntry.amount), else_=0)),0)).filter(models.LedgerEntry.account_id == account.id).scalar()

    return {"Balance":balance}

@router.get("/{id}/transactions", response_model=List[schemas.TransactionsResponse])
def check_transactions(id:int = id, db: Session= Depends(get_db), current_user :dict =Depends(get_regular_user)):
    account = db.query(models.Account).filter(models.Account.user_id== current_user.id).filter(models.Account.id == id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    transactions = db.query(models.Transaction).filter(or_(models.Transaction.from_account_id == id, models.Transaction.to_account_id ==id)).order_by(models.Transaction.created_at.desc(),models.Transaction.id.desc()).all()
    return transactions