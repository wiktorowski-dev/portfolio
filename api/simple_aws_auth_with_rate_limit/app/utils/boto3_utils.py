import asyncio
from concurrent.futures import ThreadPoolExecutor
from functools import wraps, partial
import cachetools.func
import os
import boto3
import json


def get_cognito_credentials():
    """Caching internally function, to do not use os.env on startup"""

    # Declare a static variable to hold the cached function
    if not hasattr(get_cognito_credentials, "cached_get_secret"):
        # Define the internal function and apply caching
        @cachetools.func.ttl_cache(maxsize=0 if os.environ.get('ENV') == 'pytest' else 1, ttl=1200)
        def get_secret():
            return json.loads(
                boto3.client('secretsmanager').get_secret_value(SecretId=os.environ.get('cognito_secret'))['SecretString'])

        # Store the cached version of the function
        get_cognito_credentials.cached_get_secret = get_secret

    # Use the cached version of get_secret
    secret = get_cognito_credentials.cached_get_secret()
    return secret


def cover_sync_as_async(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        executor = ThreadPoolExecutor()
        loop = asyncio.get_event_loop()
        partial_func = partial(func, *args, **kwargs)
        result = await loop.run_in_executor(executor, partial_func)
        return result

    return wrapper


@cover_sync_as_async
def sign_up_user_cognito_async(client_id, username: str, password: str, user_attributes: list):
    cognito_client = boto3.client("cognito-idp", region_name=get_cognito_credentials()['COGNITO_REGION'])
    response = cognito_client.sign_up(
        ClientId=client_id,
        Username=username,
        Password=password,
        UserAttributes=user_attributes
    )

    return response


@cover_sync_as_async
def initiate_auth_cognito_async(client_id, auth_flow, auth_parameters):
    cognito_client = boto3.client("cognito-idp", region_name=get_cognito_credentials()['COGNITO_REGION'])
    response = cognito_client.initiate_auth(
        ClientId=client_id,
        AuthFlow=auth_flow,
        AuthParameters=auth_parameters
    )

    return response


@cover_sync_as_async
def resend_confirmation_code_cognito_async(client_id, username: str):
    cognito_client = boto3.client("cognito-idp", region_name=get_cognito_credentials()['COGNITO_REGION'])
    response = cognito_client.resend_confirmation_code(
        ClientId=client_id,
        Username=username
    )

    return response


@cover_sync_as_async
def forgot_password_cognito_async(client_id, username: str):
    cognito_client = boto3.client("cognito-idp", region_name=get_cognito_credentials()['COGNITO_REGION'])
    response = cognito_client.forgot_password(
        ClientId=client_id,
        Username=username
    )

    return response


@cover_sync_as_async
def confirm_forgot_password_cognito_async(client_id, username: str, confirmation_code, password: str):
    cognito_client = boto3.client("cognito-idp", region_name=get_cognito_credentials()['COGNITO_REGION'])
    response = cognito_client.confirm_forgot_password(
        ClientId=client_id,
        Username=username,
        ConfirmationCode=confirmation_code,
        Password=password
    )

    return response


@cover_sync_as_async
def change_password_cognito_async(access_token, previous_password, proposed_password):
    cognito_client = boto3.client("cognito-idp", region_name=get_cognito_credentials()['COGNITO_REGION'])
    response = cognito_client.change_password(
        AccessToken=access_token,
        PreviousPassword=previous_password,
        ProposedPassword=proposed_password
    )

    return response
