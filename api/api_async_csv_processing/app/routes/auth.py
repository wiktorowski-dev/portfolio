from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm
from app.models.user import UserCreate, TokenResponse
from app.utils import auth
from app.crud import users
from app.dependencies import db_session as db_session_dependency
from app import exceptions

router = APIRouter()


@router.post("/sign_in", response_model=TokenResponse)
async def sign_in(
        form_data: OAuth2PasswordRequestForm = Depends(),
        db_session=Depends(db_session_dependency.get_db_session)
):
    db_user = await users.get_user_by_email(db_session, form_data.username)
    if not db_user or not auth.verify_password(form_data.password, db_user.password_hash):
        raise exceptions.INVALID_CREDENTIALS

    token = auth.create_access_token({"sub": db_user.email})
    return TokenResponse(access_token=token)


@router.post("/sign_up")
async def sign_up(
        user: UserCreate,
        db_session=Depends(db_session_dependency.get_db_session)
):
    existing = await users.get_user_by_email(db_session, user.email)
    if existing:
        raise exceptions.USER_ALREADY_EXISTS

    hashed = auth.hash_password(user.password)
    await users.create_user(db_session, user.email, hashed)
    return JSONResponse(status_code=status.HTTP_201_CREATED, content={"email": user.email})
