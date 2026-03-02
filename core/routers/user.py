from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import schemas, utils, models
from sqlalchemy.exc import IntegrityError

from database import get_db
router = APIRouter(prefix="/register")

@router.post("/")
def create_user(user: schemas.User, db: Session= Depends(get_db)):
    user.email = user.email.lower()
    user.password = utils.hash_password(user.password)
    try:
        new = models.User(**user.model_dump())
        db.add(new)
        db.commit()
        db.refresh(new)
    except IntegrityError:
        raise HTTPException(status_code=409, detail="User already exists")
    return new



    