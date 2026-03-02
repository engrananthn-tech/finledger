from fastapi import FastAPI
from routers import user, account, deposit, auth, callback, withdrawal, transfer
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta, timezone
from database import SessionLocal
import models
import schemas

app = FastAPI()

def expire_pending_transactions():
    db = SessionLocal()
    try:
        cutoff = datetime.now(timezone.utc) - timedelta(minutes=10)
        pending_transactions = db.query(models.Transaction).filter(
            models.Transaction.status == schemas.TransactionStatus.pending,
            models.Transaction.created_at < cutoff
        ).all()
        for r in pending_transactions:
            r.status ==schemas.TransactionStatus.failed
            audit = models.AuditLog(entity_type=schemas.EntityType.transaction, entity_id = r.id, action =schemas.Action.expired, actor_type= schemas.ActorType.system)
            db.add(audit)
        db.commit()
    finally:
        db.close()

scheduler = BackgroundScheduler()
scheduler.add_job(expire_pending_transactions, 'interval', minutes=10)
scheduler.start()

app.include_router(user.router)
app.include_router(account.router)
app.include_router(deposit.router)
app.include_router(auth.router)
app.include_router(callback.router)
app.include_router(withdrawal.router)
app.include_router(transfer.router)

