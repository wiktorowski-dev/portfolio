from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError

from app.utils.auth import decode_access_token
from app import exceptions

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/sign_in")


async def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        email = decode_access_token(token)
        return email
    except JWTError:
        raise exceptions.INVALID_TOKEN
