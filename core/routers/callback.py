from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import schemas, utils, models
from sqlalchemy.exc import IntegrityError
import uuid
import httpx
from oauth2 import get_current_user
from database import get_db
from fastapi import Request
from config import settings

router = APIRouter(prefix="/bank", tags=['Bank'])

@router.post("/callback")
async def bank_callback(payload: schemas.BankCallbackInput, db: Session = Depends(get_db)):
    print("hello")
    if payload.secret_key != settings.BANK_WEBHOOK_SECRET:
        raise HTTPException(status_code=401)
    with db.begin():
        transaction =db.query(models.Transaction).filter(models.Transaction.reference_id == payload.reference_id).first() 
        if not transaction:
            return {"ok": True}

        if transaction.status != schemas.TransactionStatus.pending:
            return {"ok": True}

        if payload.status == schemas.TransactionStatus.settled:
            transaction.status = schemas.TransactionStatus.settled
            audit = models.AuditLog(entity_type=schemas.EntityType.transaction, entity_id = transaction.id, action =schemas.Action.settled, actor_type= schemas.ActorType.system)
            if transaction.from_account_id:
                account_id = transaction.from_account_id
            else:
                account_id = transaction.to_account_id
            user_account = db.query(models.Account).filter(
                models.Account.id == account_id
            ).first()

            platform_cash_account = db.query(models.Account).filter(models.Account.account_type == schemas.AccountType.system).filter(models.Account.name == schemas.SystemAccountName.platform_cash).first()
            platform_revenue_account = db.query(models.Account).filter(models.Account.account_type == schemas.AccountType.system).filter(models.Account.name == schemas.SystemAccountName.platform_revenue).first()
            amount = transaction.amount-transaction.fee
            if transaction.type == schemas.TransactionType.deposit:
                entry1=models.LedgerEntry(account_id=user_account.id,amount=transaction.amount,direction=schemas.LedgerDirection.credit,reference_id=payload.reference_id)
                entry2 =models.LedgerEntry(account_id=platform_cash_account.id,amount=transaction.amount-transaction.fee,direction=schemas.LedgerDirection.debit,reference_id=payload.reference_id)
                db.add(entry1)
                db.add(entry2)
                db.flush()
                audit1 = models.AuditLog(entity_type=schemas.EntityType.ledger, entity_id = entry1.id, action =schemas.Action.created, actor_type= schemas.ActorType.system)
                audit2 = models.AuditLog(entity_type=schemas.EntityType.ledger, entity_id = entry2.id, action =schemas.Action.created, actor_type= schemas.ActorType.system)
                db.add(audit1)
                db.add(audit2)
            else:
                entry1=models.LedgerEntry(account_id=user_account.id,amount=transaction.amount,direction=schemas.LedgerDirection.debit,reference_id=payload.reference_id)
                entry2 =models.LedgerEntry(account_id=platform_cash_account.id,amount=transaction.amount-transaction.fee,direction=schemas.LedgerDirection.credit,reference_id=payload.reference_id) 
                entry3 =models.LedgerEntry(account_id=platform_revenue_account.id,amount=transaction.fee,direction=schemas.LedgerDirection.credit,reference_id=payload.reference_id)
                db.add(entry1)
                db.add(entry2)
                db.add(entry3)
                db.flush()
                audit1 = models.AuditLog(entity_type=schemas.EntityType.ledger, entity_id = entry1.id, action =schemas.Action.created, actor_type= schemas.ActorType.system)
                audit2 = models.AuditLog(entity_type=schemas.EntityType.ledger, entity_id = entry2.id, action =schemas.Action.created, actor_type= schemas.ActorType.system)
                audit3 = models.AuditLog(entity_type=schemas.EntityType.ledger, entity_id = entry2.id, action =schemas.Action.created, actor_type= schemas.ActorType.system)
                db.add(audit1)
                db.add(audit2)
                db.add(audit3)

        else:
            transaction.status = schemas.TransactionStatus.failed
            audit = models.AuditLog(entity_type=schemas.EntityType.transaction, entity_id = transaction.id, action =schemas.Action.failed, actor_type= schemas.ActorType.system)
            db.add(audit)

    return {"ok": True}
    