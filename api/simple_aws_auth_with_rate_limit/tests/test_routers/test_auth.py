import asyncio
import boto3
from fastapi.testclient import TestClient
import os
from app import exceptions
from app.crud import user as user_crud
from app.utils import boto3_utils
from main import app
from tests.mockers.aws_mock import mock_aws_custom
from tests.mockers.sql_mockers import mock_sql_decorator
from tests.mockers.generic_mock import mock_generic_decorator
from tests.common.user_credentials import User

client = TestClient(app)


def get_token():
    response = client.post("/auth/sign_in", data={"username": User.email, "password": User.password})
    assert response.status_code == 200
    assert "access_token" in response.json()
    return response.json()["access_token"]


def get_auth_headers():
    token = get_token()
    headers = {"Authorization": f"Bearer {token}"}
    return headers


@mock_generic_decorator
@mock_sql_decorator
@mock_aws_custom
def test_create_user_success():
    cognito_client = boto3.client('cognito-idp')
    # Check len(users)
    cognito_users = cognito_client.list_users(UserPoolId=boto3_utils.get_cognito_credentials()['COGNITO_USER_POOL_ID'])
    assert len(cognito_users['Users']) == 1

    user_email = 'new_user@example.com'
    response = client.post(
        "/auth/sign_up",
        json={
            "email": user_email,
            "password": User.password,
            "newsletter_subscribed": True
        }
    )

    assert response.status_code == 200

    # Cognito Check
    cognito_users = cognito_client.list_users(UserPoolId=boto3_utils.get_cognito_credentials()['COGNITO_USER_POOL_ID'])
    assert len(cognito_users['Users']) == 2

    # SQL Check
    user = asyncio.run(user_crud.get_user_by_email(email=user_email))
    assert user.email == user_email


@mock_generic_decorator
@mock_sql_decorator
@mock_aws_custom
def test_create_user_success_and_login():
    user_email = 'new_user@example.com'
    response = client.post(
        "/auth/sign_up",
        json={
            "email": user_email,
            "password": User.password,
            "newsletter_subscribed": True
        }
    )

    assert response.status_code == 200

    cognito_client = boto3.client('cognito-idp')
    cognito_client.admin_confirm_sign_up(
        UserPoolId=boto3_utils.get_cognito_credentials()['COGNITO_USER_POOL_ID'],
        Username=user_email
    )

    login_response = client.post(
        "/auth/sign_in",
        data={
            "username": user_email,
            "password": User.password
        }
    )
    assert login_response.status_code == 200

    headers = get_auth_headers()
    access_token = headers['Authorization'].split(' ')[-1]
    assert access_token, "Access token missing"


@mock_generic_decorator
@mock_sql_decorator
@mock_aws_custom
def test_create_user_without_password():
    response = client.post(
        "/auth/sign_up",
        json={
            "email": 'new_user@example.com',
            "newsletter_subscribed": True
        }
    )

    assert response.status_code == 422
    assert response.json()['detail'][0]['loc'][1] + ' ' + response.json()['detail'][0]['type'] == 'password missing'


@mock_generic_decorator
@mock_sql_decorator
@mock_aws_custom
def test_create_user_without_username():
    response = client.post(
        "/auth/sign_up",
        json={
            "password": User.password,
            "newsletter_subscribed": True
        }
    )

    assert response.status_code == 422
    assert response.json()['detail'][0]['loc'][1] + ' ' + response.json()['detail'][0]['type'] == 'email missing'


@mock_generic_decorator
@mock_sql_decorator
@mock_aws_custom
def test_create_user_without_username():
    response = client.post(
        "/auth/sign_up",
        json={
            "email": 'new_user@example.com',
            "password": User.password
        }
    )

    assert response.status_code == 422
    assert response.json()['detail'][0]['loc'][1] + ' ' + response.json()['detail'][0]['type'] == 'newsletter_subscribed missing'

    cognito_client = boto3.client('cognito-idp')
    cognito_users = cognito_client.list_users(UserPoolId=boto3_utils.get_cognito_credentials()['COGNITO_USER_POOL_ID'])
    assert len(cognito_users['Users']) == 1


@mock_generic_decorator
@mock_sql_decorator
@mock_aws_custom
def test_create_user_already_exists():
    cognito_client = boto3.client('cognito-idp')
    cognito_users = cognito_client.list_users(UserPoolId=boto3_utils.get_cognito_credentials()['COGNITO_USER_POOL_ID'])
    assert len(cognito_users['Users']) == 1

    response = client.post(
        "/auth/sign_up",
        json={
            "email": User.email,
            "password": User.password,
            "newsletter_subscribed": True
        }
    )
    assert response.status_code == exceptions.USERNAME_ALREADY_EXISTS.status_code
    assert response.json()["detail"] == exceptions.USERNAME_ALREADY_EXISTS.detail

    cognito_client = boto3.client('cognito-idp')
    cognito_users = cognito_client.list_users(UserPoolId=boto3_utils.get_cognito_credentials()['COGNITO_USER_POOL_ID'])
    assert len(cognito_users['Users']) == 1


@mock_generic_decorator
@mock_sql_decorator
@mock_aws_custom
def test_create_user_passwort_too_short():
    response = client.post(
        "/auth/sign_up",
        json={
            "email": "new_user@example.com",
            "password": "Passwor",
            "newsletter_subscribed": True
        }
    )

    assert response.status_code == exceptions.PASSWORD_TOO_SHORT.status_code

    cognito_client = boto3.client('cognito-idp')
    cognito_users = cognito_client.list_users(UserPoolId=boto3_utils.get_cognito_credentials()['COGNITO_USER_POOL_ID'])
    assert len(cognito_users['Users']) == 1


@mock_generic_decorator
@mock_sql_decorator
@mock_aws_custom
def test_create_user_passwort_without_uppercase():
    response = client.post(
        "/auth/sign_up",
        json={
            "email": "new_user@example.com",
            "password": "password12!",
            "newsletter_subscribed": True
        }
    )

    assert response.status_code == exceptions.PASSWORD_WITHOUT_UPPERCASE.status_code

    cognito_client = boto3.client('cognito-idp')
    cognito_users = cognito_client.list_users(UserPoolId=boto3_utils.get_cognito_credentials()['COGNITO_USER_POOL_ID'])
    assert len(cognito_users['Users']) == 1


@mock_generic_decorator
@mock_sql_decorator
@mock_aws_custom
def test_create_user_passwort_without_lowercase():
    response = client.post(
        "/auth/sign_up",
        json={
            "email": "new_user@example.com",
            "password": "PASSWORD12!",
            "newsletter_subscribed": True
        }
    )

    assert response.status_code == exceptions.PASSWORD_WITHOUT_LOWERCASE.status_code

    cognito_client = boto3.client('cognito-idp')
    cognito_users = cognito_client.list_users(UserPoolId=boto3_utils.get_cognito_credentials()['COGNITO_USER_POOL_ID'])
    assert len(cognito_users['Users']) == 1


@mock_generic_decorator
@mock_sql_decorator
@mock_aws_custom
def test_create_user_passwort_without_number():
    response = client.post(
        "/auth/sign_up",
        json={
            "email": "new_user@example.com",
            "password": "Password!",
            "newsletter_subscribed": True
        }
    )

    assert response.status_code == exceptions.PASSWORD_WITHOUT_NUMBER.status_code

    cognito_client = boto3.client('cognito-idp')
    cognito_users = cognito_client.list_users(UserPoolId=boto3_utils.get_cognito_credentials()['COGNITO_USER_POOL_ID'])
    assert len(cognito_users['Users']) == 1


@mock_generic_decorator
@mock_sql_decorator
@mock_aws_custom
def test_login_success():
    response = client.post(
        "/auth/sign_in",
        data={
            "username": User.username,
            "password": User.password
        }
    )

    assert response.status_code == 200

    headers = get_auth_headers()
    access_token = headers['Authorization'].split(' ')[-1]
    assert access_token, "Access token missing"


@mock_generic_decorator
@mock_sql_decorator
@mock_aws_custom
def test_login_without_username():
    response = client.post(
        "/auth/sign_in",
        data={
            "password": User.password
        }
    )

    assert response.status_code == 422
    assert response.json()['detail'][0]['loc'][1] + ' ' + response.json()['detail'][0]['type'] == 'username missing'


@mock_generic_decorator
@mock_sql_decorator
@mock_aws_custom
def test_login_without_password():
    response = client.post(
        "/auth/sign_in",
        data={
            "username": User.username
        }
    )

    assert response.status_code == 422
    assert response.json()['detail'][0]['loc'][1] + ' ' + response.json()['detail'][0]['type'] == 'password missing'


@mock_generic_decorator
@mock_sql_decorator
@mock_aws_custom
def test_login_bad_username():
    response = client.post(
        "/auth/sign_in",
        data={
            "username": 'userexample.com',
            "password": User.password
        }
    )

    assert response.status_code == exceptions.INCORRECT_USERNAME_OR_PASSWORD.status_code
    assert response.json()["detail"] == exceptions.INCORRECT_USERNAME_OR_PASSWORD.detail


@mock_generic_decorator
@mock_sql_decorator
@mock_aws_custom
def test_login_bad_passwort():
    response = client.post(
        "/auth/sign_in",
        data={
            "username": User.username,
            "password": 'BADpass12!'
        }
    )

    assert response.status_code == exceptions.INCORRECT_USERNAME_OR_PASSWORD.status_code
    assert response.json()["detail"] == exceptions.INCORRECT_USERNAME_OR_PASSWORD.detail


@mock_generic_decorator
@mock_sql_decorator
@mock_aws_custom
def test_resend_activation_link():
    """Moto functionality do not allow to test this case. It is not possible to resend confirmation code."""
    assert True


@mock_generic_decorator
@mock_sql_decorator
@mock_aws_custom
def test_resend_activation_link_email_without_domain():
    response = client.post(
        "/auth/resend_activation_link",
        json={
            "email": "user@example"
        }
    )

    assert response.status_code == 422
    assert response.json()["detail"][0]["ctx"]["reason"] == \
           'The part after the @-sign is not valid. It should have a period.'


@mock_generic_decorator
@mock_sql_decorator
@mock_aws_custom
def test_resend_activation_link_email_without_sign():
    response = client.post(
        "/auth/resend_activation_link",
        json={
            "email": "userexample.com"
        }
    )

    assert response.status_code == 422
    assert response.json()["detail"][0]["ctx"]["reason"] == 'An email address must have an @-sign.'


@mock_generic_decorator
@mock_sql_decorator
@mock_aws_custom
def test_forgot_password():
    response = client.post(
        "/auth/forgot-password",
        json={
            "email": "user@example.com"
        }
    )

    assert response.status_code == 200


@mock_generic_decorator
@mock_sql_decorator
@mock_aws_custom
def test_forgot_password_without_email():
    response = client.post(
        "/auth/forgot-password",
        json={
        }
    )

    assert response.status_code == 422
    assert response.json()['detail'][0]['loc'][1] + ' ' + response.json()['detail'][0]['type'] == 'email missing'


@mock_generic_decorator
@mock_sql_decorator
@mock_aws_custom
def test_forgot_password_email_without_domain():
    response = client.post(
        "/auth/forgot-password",
        json={
            "email": "user@example"
        }
    )

    assert response.status_code == 422
    assert response.json()["detail"][0]["ctx"]["reason"] == \
           'The part after the @-sign is not valid. It should have a period.'


@mock_generic_decorator
@mock_sql_decorator
@mock_aws_custom
def test_forgot_password_email_without_sign():
    response = client.post(
        "/auth/forgot-password",
        json={
            "email": "userexample.com"
        }
    )

    assert response.status_code == 422
    assert response.json()["detail"][0]["ctx"]["reason"] == 'An email address must have an @-sign.'


@mock_generic_decorator
@mock_sql_decorator
@mock_aws_custom
def test_confirm_forgot_password():
    """Moto functionality do not allow to test this case. It is not possible to resend confirmation code."""
    assert True


@mock_generic_decorator
@mock_sql_decorator
@mock_aws_custom
def test_change_password():
    login_response = client.post(
        "/auth/sign_in",
        data={
            "username": User.username,
            "password": User.password
        }
    )

    assert login_response.status_code == 200

    headers = get_auth_headers()
    access_token = headers['Authorization'].split(' ')[-1]

    new_password = '123Zgytuawi!@'
    response = client.post(
        "/auth/change-password",
        json={
            "token": access_token,
            "previous_password": User.password,
            "proposed_password": new_password
        },
        headers=headers
    )

    assert response.status_code == 200

    # Check old password
    login_response = client.post(
        "/auth/sign_in",
        data={
            "username": User.username,
            "password": User.password
        }
    )
    assert login_response.status_code == exceptions.INCORRECT_USERNAME_OR_PASSWORD.status_code

    # Check new password
    login_response = client.post(
        "/auth/sign_in",
        data={
            "username": User.username,
            "password": new_password
        }
    )
    assert login_response.status_code == 200


@mock_generic_decorator
@mock_sql_decorator
@mock_aws_custom
def test_change_password_without_login():
    response = client.post(
        "/auth/change-password",
        json={
            "previous_password": User.password,
            "proposed_password": f'{User.password}12'
        }
    )

    assert response.status_code == 401
    assert response.json()['detail'] == 'Not authenticated'


@mock_generic_decorator
@mock_sql_decorator
@mock_aws_custom
def test_change_password_without_token():
    login_response = client.post(
        "/auth/sign_in",
        data={
            "username": User.username,
            "password": User.password
        }
    )

    assert login_response.status_code == 200

    headers = get_auth_headers()

    new_password = '123Zgytuawi!@'
    response = client.post(
        "/auth/change-password",
        json={
            "previous_password": User.password,
            "proposed_password": new_password
        },
        headers=headers
    )

    assert response.status_code == 422
    assert response.json()['detail'][0]['loc'][1] + ' ' + response.json()['detail'][0]['type'] == 'token missing'


@mock_generic_decorator
@mock_sql_decorator
@mock_aws_custom
def test_change_password_without_previous_password():
    login_response = client.post(
        "/auth/sign_in",
        data={
            "username": User.username,
            "password": User.password
        }
    )

    assert login_response.status_code == 200

    headers = get_auth_headers()
    access_token = headers['Authorization'].split(' ')[-1]

    new_password = '123Zgytuawi!@'
    response = client.post(
        "/auth/change-password",
        json={
            "token": access_token,
            "proposed_password": new_password
        },
        headers=headers
    )

    assert response.status_code == 422
    assert response.json()['detail'][0]['loc'][1] + ' ' + response.json()['detail'][0]['type'] == 'previous_password missing'


@mock_generic_decorator
@mock_sql_decorator
@mock_aws_custom
def test_change_password_without_proposed_password():
    login_response = client.post(
        "/auth/sign_in",
        data={
            "username": User.username,
            "password": User.password
        }
    )

    assert login_response.status_code == 200

    headers = get_auth_headers()
    access_token = headers['Authorization'].split(' ')[-1]

    response = client.post(
        "/auth/change-password",
        json={
            "token": access_token,
            "previous_password": User.password
        },
        headers=headers
    )

    assert response.status_code == 422
    assert response.json()['detail'][0]['loc'][1] + ' ' + response.json()['detail'][0]['type'] == 'proposed_password missing'


@mock_generic_decorator
@mock_sql_decorator
@mock_aws_custom
def test_change_password_bad_password():
    # short, uppercase, lowercase, number
    bad_password = ['Passwor', 'password12!', 'PASSWORD12!', 'Password!']
    for psw in bad_password:
        login_response = client.post(
            "/auth/sign_in",
            data={
                "username": User.username,
                "password": User.password
            }
        )

        assert login_response.status_code == 200

        headers = get_auth_headers()
        access_token = headers['Authorization'].split(' ')[-1]

        response = client.post(
            "/auth/change-password",
            json={
                "token": access_token,
                "previous_password": User.password,
                "proposed_password": psw
            },
            headers=headers
        )

        assert response.status_code == 400


@mock_generic_decorator
@mock_sql_decorator
@mock_aws_custom
def test_change_password_bad_user_password():
    login_response = client.post(
        "/auth/sign_in",
        data={
            "username": User.username,
            "password": User.password
        }
    )

    assert login_response.status_code == 200

    headers = get_auth_headers()
    access_token = headers['Authorization'].split(' ')[-1]

    new_password = '123Zgytuawi!@'
    response = client.post(
        "/auth/change-password",
        json={
            "token": access_token,
            "previous_password": 'BadUserPass1!',
            "proposed_password": new_password
        },
        headers=headers
    )

    assert response.status_code == 401


@mock_generic_decorator
@mock_sql_decorator
@mock_aws_custom
def test_change_password_bad_token():
    login_response = client.post(
        "/auth/sign_in",
        data={
            "username": User.username,
            "password": User.password
        }
    )

    assert login_response.status_code == 200

    headers = get_auth_headers()
    access_token = headers['Authorization'].split(' ')[-1]

    new_password = '123Zhyuoi!@'
    response = client.post(
        "/auth/change-password",
        json={
            "token": f'{access_token}bad',
            "previous_password": User.password,
            "proposed_password": new_password
        },
        headers=headers
    )

    assert response.status_code == 401
