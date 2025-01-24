from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from passlib.context import CryptContext

from config.database import get_db
from config.models import Member

from .register_schemas import RegisterUser

register_router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
    responses={404: {"description": "Not found"}},
)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    """비밀번호 해싱"""
    return pwd_context.hash(password)

@register_router.post("/register", status_code=status.HTTP_201_CREATED)
def register_user(user: RegisterUser, db: Session = Depends(get_db)):
    """회원가입"""
    # 기존 사용자 체크
    existing_user = db.query(Member).filter(
        (Member.username == user.username) | (Member.email == user.email)
    ).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or email already registered",
        )

    # 새 사용자 생성
    new_user = Member(
        username=user.username,
        email=user.email,
        hashed_password=hash_password(user.password),
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"message": "User registered successfully", "username": new_user.username}
