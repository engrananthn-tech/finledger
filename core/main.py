from fastapi import FastAPI
from routers import user, account, deposit, auth, callback, withdrawal, transfer, admin
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta, timezone
from database import SessionLocal
import models
import schemas
from sqlalchemy.orm import Session
from contextlib import asynccontextmanager
import schemas
from fastapi.responses import HTMLResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from limiter import limiter
from fastapi.middleware.cors import CORSMiddleware



@asynccontextmanager
async def lifespan(app: FastAPI):
    db = SessionLocal()
    seed_system_accounts(db)
    db.close()
    yield

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

def expire_pending_transactions():
    db = SessionLocal()
    try:
        cutoff = datetime.now(timezone.utc) - timedelta(minutes=10)
        pending_transactions = db.query(models.Transaction).filter(
            models.Transaction.status == schemas.TransactionStatus.pending,
            models.Transaction.created_at < cutoff
        ).all()
        for r in pending_transactions:
            r.status = schemas.TransactionStatus.failed
            audit = models.AuditLog(entity_type=schemas.EntityType.transaction, entity_id = r.id, action =schemas.Action.expired, actor_type= schemas.ActorType.system)
            db.add(audit)
        db.commit()
    finally:
        db.close()

scheduler = BackgroundScheduler()
scheduler.add_job(expire_pending_transactions, 'interval', minutes=10)
scheduler.start()

def seed_system_accounts(db: Session):

    for name in schemas.SystemAccountName:
        exists = db.query(models.Account).filter(models.Account.name == name).first()
        if not exists:
            db.add(models.Account(account_type=schemas.AccountType.system, name=name))
    db.commit()

@app.get("/", response_class=HTMLResponse)
def home():
    return """
    <html>
        <head><title>API Server</title></head>
        <body>
            <h1>Backend Running</h1>
            <p>If you're a developer:
Open /docs to explore and test the API.<p>

<p>If you're reviewing the project:
See the GitHub repository for architecture and implementation details.</p>
<p><a href="https://github.com/engrananthn-tech/finledger">Git hub repo<a><p>
        </body>
    </html>
    """

app.include_router(user.router)
app.include_router(account.router)
app.include_router(deposit.router)
app.include_router(auth.router)
app.include_router(callback.router)
app.include_router(withdrawal.router)
app.include_router(transfer.router)
app.include_router(admin.router)

