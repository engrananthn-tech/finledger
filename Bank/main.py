from fastapi import FastAPI, Depends
from database import get_db
from sqlalchemy.orm import Session
import models, schemas
import time, random
import httpx
from config import settings

app = FastAPI()

@app.post("/bank/deposits")
async def bank_deposit(input: schemas.TransferInput, db: Session = Depends(get_db)): 
    with db.begin():
        new = models.BankTransfer(reference_id = input.reference_id, amount= input.amount, direction=schemas.BankDirection.OUT, status=schemas.TransferStatus.pending)
        db.add(new)
    # time.sleep(random.randint(1,30))
    chance = random.choice([True, False])
    if 1:
         status= schemas.TransferStatus.settled
    else:
         status= schemas.TransferStatus.failed
    transfer=db.query(models.BankTransfer).filter(models.BankTransfer.reference_id == input.reference_id).first()
    transfer.status=status
    db.commit()
    print("hi")
    async with httpx.AsyncClient() as client:
            await client.post(
                "https://finance-ledger-uux3.onrender.com/bank/callback",
                json={"reference_id": str(input.reference_id), "status": status.value, "secret_key": settings.BANK_WEBHOOK_SECRET}
            )

@app.post("/bank/withdrawals")
async def bank_withdraw(input: schemas.TransferInput, db: Session = Depends(get_db)):
    with db.begin():
        new = models.BankTransfer(reference_id = input.reference_id, amount= input.amount, direction=schemas.BankDirection.IN, status=schemas.TransferStatus.pending)
        db.add(new)
    chance = random.choice([True, False])
    if 1:
        status= schemas.TransferStatus.settled
    else:
        status= schemas.TransferStatus.failed
        
    transfer=db.query(models.BankTransfer).filter(models.BankTransfer.reference_id == input.reference_id).first()
    transfer.status=status
    db.commit()
    async with httpx.AsyncClient() as client:
            await client.post(
                "https://finance-ledger-uux3.onrender.com/bank/callback",
                json={"reference_id": str(input.reference_id), "status": status.value, "secret_key": settings.BANK_WEBHOOK_SECRET}
            )




    

    