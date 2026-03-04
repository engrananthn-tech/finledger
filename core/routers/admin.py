from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import schemas, models
from database import get_db
from oauth2 import get_current_user
from typing import List
from sqlalchemy import func, case
router = APIRouter(prefix="/admin", tags=['admin'])



def get_admin_user(current_user = Depends(get_current_user)):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admins only")
    return current_user

@router.get("/transactions", response_model=List[schemas.TransactionsResponse])
def get_all_transactions(limit: int = 20,offset: int = 0, db: Session = Depends(get_db), current_user: dict = Depends(get_admin_user)):
    transactions = db.query(models.Transaction).order_by(models.Transaction.created_at.desc(),models.Transaction.id.desc()).offset(offset).limit(limit).all()
    return transactions

@router.get("/ledger", response_model=List[schemas.LedgerEntryResponse])
def get_all_ledgerentries(limit: int = 20,offset: int = 0,db: Session = Depends(get_db), current_user: dict = Depends(get_admin_user)):
    ledger_entries = db.query(models.LedgerEntry).order_by(models.Transaction.created_at.desc(),models.Transaction.id.desc()).offset(offset).limit(limit).all
    return ledger_entries

@router.get("/accounts", response_model=List[schemas.AccountResponse])
def get_all_accounts( limit: int = 20,offset: int = 0, db: Session = Depends(get_db), current_user: dict = Depends(get_admin_user)):
    accounts = db.query(models.Account).order_by(models.Account.id).offset(offset).limit(limit).all()
    return accounts


@router.get("/accounts/{id}/balances")
def check_balance( db: Session = Depends(get_db), current_user: dict = Depends(get_admin_user)):
    balance=  db.query(func.coalesce(func.sum(case((models.LedgerEntry.direction == schemas.LedgerDirection.credit, models.LedgerEntry.amount),(models.LedgerEntry.direction == schemas.LedgerDirection.debit, -models.LedgerEntry.amount), else_=0)),0)).filter(models.LedgerEntry.account_id == id).scalar()
    
    return schemas.BalanceResponse(account_id=id, balance=balance)

@router.get("/auditlogs", response_model=List[schemas.AuditLogResponse])
def get_audit_logs(limit: int = 20,offset: int = 0, db: Session = Depends(get_db), current_user: dict = Depends(get_admin_user)):
    audit_logs = db.query(models.AuditLog).order_by(models.AuditLog.created_at.desc()).offset(offset).limit(limit).all()
    return audit_logs