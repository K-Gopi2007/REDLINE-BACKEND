from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import verify_password, get_password_hash, create_access_token
from app.models.user import User
from app.schemas.user import UserCreate, UserResponse
from app.schemas.token import Token
from app.api.deps import get_current_user
from pydantic import BaseModel
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

router = APIRouter()

import logging
import traceback

logger = logging.getLogger(__name__)

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    try:
        user = db.query(User).filter(User.email == user_in.email).first()
        if user:
            from fastapi.responses import JSONResponse
            return JSONResponse(
                status_code=400,
                content={
                    "error": "duplicate_email",
                    "message": "The user with this email already exists in the system."
                }
            )
        hashed_password = get_password_hash(user_in.password)
        db_user = User(email=user_in.email, hashed_password=hashed_password)
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration failed: {e}\n{traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail={"error": "Internal server error", "message": str(e)}
        )

@router.post("/login", response_model=Token)
def login(db: Session = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()):
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    
    access_token = create_access_token(subject=user.email)
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=UserResponse)
def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user

class GoogleAuthRequest(BaseModel):
    credential: str

@router.post("/google", response_model=Token)
def google_login(request: GoogleAuthRequest, db: Session = Depends(get_db)):
    import requests
    try:
        if request.credential.count('.') == 2:
            # It's a JWT
            from app.core.config import settings
            idinfo = id_token.verify_oauth2_token(request.credential, google_requests.Request(), audience=settings.GOOGLE_CLIENT_ID if settings.GOOGLE_CLIENT_ID else None)
            email = idinfo.get("email")
        else:
            # It's an access token
            from app.core.config import settings
            tokeninfo_resp = requests.get(f"https://oauth2.googleapis.com/tokeninfo?access_token={request.credential}")
            if tokeninfo_resp.status_code != 200:
                raise ValueError("Invalid access token")
            tokeninfo = tokeninfo_resp.json()
            if settings.GOOGLE_CLIENT_ID and tokeninfo.get("aud") != settings.GOOGLE_CLIENT_ID:
                raise ValueError("Token was not issued for this client ID")
            email = tokeninfo.get("email")
            
        if not email:
            raise HTTPException(status_code=400, detail="No email provided in Google token")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid Google token")

    user = db.query(User).filter(User.email == email).first()
    if not user:
        # Create user if not exists
        db_user = User(email=email, hashed_password="")
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        user = db_user

    access_token = create_access_token(subject=user.email)
    return {"access_token": access_token, "token_type": "bearer"}
