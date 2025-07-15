from fastapi import APIRouter, Depends

from app.dependencies.auth import get_current_user


router = APIRouter()


@router.get("/me")
async def read_users_me(user_email: str = Depends(get_current_user)):
    return {"email": user_email}