import json

from moto import mock_aws
import requests_mock
from contextlib import contextmanager
import os
import functools
import boto3
import inspect
import asyncio
from functools import wraps

from tests.common.user_credentials import User
from tests.mockers.sql_mockers import mock_sql_decorator
from app.utils.sql_connection import SQLConnection


def mock_aws_custom_class(cls):
    """
    A decorator to mock AWS services for all methods in a class.
    This version wraps each method in the class with the mock_aws decorator.
    """
    for attr_name, attr_value in cls.__dict__.items():
        # Check if the attribute is a callable (method) and not a dunder method
        if callable(attr_value) and not attr_name.startswith("__"):
            # Wrap the method with the AWS mocking logic
            wrapped_method = mock_aws_custom(attr_value)
            # Replace the original method with the wrapped one
            setattr(cls, attr_name, wrapped_method)

    return cls


def mock_aws_custom(func):
    @mock_aws
    @requests_mock.Mocker(kw='m')
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # Set up the mocked DynamoDB environment
        set_aws_env_vars()
        create_sql_secret()
        create_cognito_user(mock=kwargs.pop('m'))

        # Call the test function
        if inspect.iscoroutinefunction(func):
            return asyncio.run(func(*args, **kwargs))
        else:
            return func(*args, **kwargs)

    return wrapper


def create_cognito_user(mock: requests_mock.Mocker):
    client = boto3.client('cognito-idp')

    # Create a Cognito User Pool
    response = client.create_user_pool(
        PoolName='test-user-pool'
    )

    user_pool_id = response['UserPool']['Id']

    # Create a User Pool Client (App Client)
    client_response = client.create_user_pool_client(
        UserPoolId=user_pool_id,
        ClientName='test-client',
        ExplicitAuthFlows=['ALLOW_USER_PASSWORD_AUTH', 'ALLOW_REFRESH_TOKEN_AUTH']
    )

    # Create a user in the user pool
    client.admin_create_user(
        UserPoolId=user_pool_id,
        Username=User.username,
        UserAttributes=[
            {'Name': 'email', 'Value': User.email},
            {'Name': 'email_verified', 'Value': 'true'}
        ],
        TemporaryPassword='Password123!'
    )

    # Confirm the user and set a permanent password
    client.admin_set_user_password(
        UserPoolId=user_pool_id,
        Username=User.username,
        Password=User.password,
        Permanent=True
    )

    jwks_url = 'https://cognito-idp.us-west-2.amazonaws.com/someuserpoolid/.well-known/jwks.json'
    mock.get(jwks_url, real_http=True)

    create_cognito_secret(
        user_pool_id=user_pool_id,
        app_client_id=client_response['UserPoolClient']['ClientId'],
        region=client.meta.region_name,
        jwks_url=jwks_url
    )


def set_aws_env_vars():
    """Set here env vars"""
    os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'


def create_cognito_secret(
        user_pool_id: str,
        app_client_id: str,
        region: str,
        jwks_url: str
):

    client = boto3.client('secretsmanager')

    # Create a secret
    secret_name = "cogntio_secret"
    secret_value = json.dumps({
        "COGNITO_REGION": region,
        "COGNITO_USER_POOL_ID": user_pool_id,
        "COGNITO_CLIENT_ID": app_client_id,
        "COGNITO_JWKS_URL":  jwks_url,
        "COGNITO_ISSUER": f'https://cognito-idp.{region}.amazonaws.com/{user_pool_id}',
    })

    create_response = client.create_secret(Name=secret_name, SecretString=secret_value)

    # Get the ARN of the created secret
    secret_arn = create_response['ARN']

    # Set the ARN as an environment variable
    os.environ['cognito_secret'] = secret_arn


def create_sql_secret():
    client = boto3.client('secretsmanager')

    # Create a secret
    secret_name = "sql_secret"
    secret_value = json.dumps({
        'user': 'user',
        'password': 'password',
        'host': "test-host",
        "port": "3306"
    })

    create_response = client.create_secret(Name=secret_name, SecretString=secret_value)

    # Get the ARN of the created secret
    secret_arn = create_response['ARN']

    # Set the ARN as an environment variable
    os.environ['sql_secret'] = secret_arn


@contextmanager
def create_user_in_sql():
    with SQLConnection(database=os.environ['ACCOUNTS_SCHEMA']) as cursor:
        query = "INSERT into users (id, email) VALUES (%s, %s, %s)"
        cursor.execute(query, (User.id, User.email))
    yield

