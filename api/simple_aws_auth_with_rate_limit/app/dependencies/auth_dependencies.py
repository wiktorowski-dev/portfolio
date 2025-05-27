import requests
from fastapi import APIRouter
import cachetools.func
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
import boto3
import asyncio

from app.models.auth import UserId, User
from app.utils.boto3_utils import cover_sync_as_async
from app.dependencies.user_dependencies import get_user_db_create_if_not_exists
from app.utils import boto3_utils


router = APIRouter()


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/sign_in")


@cover_sync_as_async
def get_jwks():
    response = requests.get(boto3_utils.get_cognito_credentials()["COGNITO_JWKS_URL"])
    response.raise_for_status()
    return response.json()


@cachetools.func.ttl_cache(maxsize=1, ttl=600)
def cache_handler_get_jwks():
    jwk = asyncio.run(get_jwks())
    return jwk


@cover_sync_as_async
def get_user_from_cognito(username: str):
    cognito_client = boto3.client("cognito-idp", region_name=boto3_utils.get_cognito_credentials()['COGNITO_REGION'])
    return cognito_client.admin_get_user(
        UserPoolId=boto3_utils.get_cognito_credentials()["COGNITO_USER_POOL_ID"],
        Username=username
    )


@cachetools.func.ttl_cache(maxsize=250, ttl=600)
def cache_handler_get_user_from_cognito(username: str):
    return asyncio.run(get_user_from_cognito(username))


def verify_token(token: str):
    try:
        # Decode and verify the JWT
        unverified_headers = jwt.get_unverified_header(token)
        jwks = cache_handler_get_jwks()
        rsa_key = {}
        for key in jwks['keys']:
            if key['kid'] == unverified_headers['kid']:
                rsa_key = {
                    'kty': key['kty'],
                    'kid': key['kid'],
                    'use': key['use'],
                    'n': key['n'],
                    'e': key['e']
                }
        if rsa_key:
            payload = jwt.decode(
                token,
                rsa_key,
                algorithms=['RS256'],
                audience=boto3_utils.get_cognito_credentials()['COGNITO_CLIENT_ID'],
                issuer=boto3_utils.get_cognito_credentials()['COGNITO_ISSUER']
            )
            return payload
        else:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials")


def _get_current_user_cognito(token: str = Depends(oauth2_scheme)) -> UserId:
    payload = verify_token(token)

    response = cache_handler_get_user_from_cognito(username=payload["username"])
    email = next(attr['Value'] for attr in response['UserAttributes'] if attr['Name'] == 'email')

    return UserId(email=email, id=payload['sub'])


async def get_current_user(user: UserId = Depends(_get_current_user_cognito)) -> UserId:
    return await get_user_db_create_if_not_exists(user)

