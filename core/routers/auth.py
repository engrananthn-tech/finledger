from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
import models, utils, oauth2
from database import get_db
from limiter import limiter
router = APIRouter(prefix= "/login", tags=['Login'])


@router.post("/")
@limiter.limit("5/minute")
def user_login(request: Request, credentials: OAuth2PasswordRequestForm = Depends(), db : Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == credentials.username).first()
    if not user:
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    if not utils.verify_password(credentials.password, user.password):
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    access_token = oauth2.create_access_token({"id":user.id})
    return {"access_token": access_token}
