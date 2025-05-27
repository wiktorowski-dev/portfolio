import logging
import os
import boto3
from fastapi import Depends, HTTPException, APIRouter
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm

from app.models import auth as auth_models
from app.dependencies.auth_dependencies import get_current_user
from app.crud import user as user_crud
from app.utils import boto3_utils
from app import exceptions

router = APIRouter()


@router.post("/sign_up")
async def create_user(user: auth_models.UserCreate):
    cognito_client = boto3.client("cognito-idp", region_name=boto3_utils.get_cognito_credentials()['COGNITO_REGION'])
    try:
        response = await boto3_utils.sign_up_user_cognito_async(
            client_id=boto3_utils.get_cognito_credentials()['COGNITO_CLIENT_ID'],
            username=user.email,
            password=user.password,
            user_attributes=[
                {'Name': 'email', 'Value': user.email}
            ]
        )
        await user_crud.create_user(
            user_id=response['UserSub'],
            user_email=user.email,
            newsletter_subscribed=user.newsletter_subscribed
        )
        return {"message": "User registered successfully", "response": response}
    except cognito_client.exceptions.UsernameExistsException:
        raise exceptions.USERNAME_ALREADY_EXISTS
    except Exception as e:
        logging.error(f"Error: {str(e)}")
        raise exceptions.USER_CODE_400


@router.post("/sign_in", response_model=auth_models.Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    cognito_client = boto3.client("cognito-idp", region_name=boto3_utils.get_cognito_credentials()['COGNITO_REGION'])
    try:
        response = await boto3_utils.initiate_auth_cognito_async(
            client_id=boto3_utils.get_cognito_credentials()["COGNITO_CLIENT_ID"],
            auth_flow='USER_PASSWORD_AUTH',
            auth_parameters={
                'USERNAME': form_data.username,
                'PASSWORD': form_data.password,
            }
        )

        access_token = response['AuthenticationResult']['AccessToken']

        # Response set cookie
        response = JSONResponse(content={"access_token": access_token, "token_type": "bearer"})
        response.set_cookie(key="access_token", value=access_token, httponly=True)
        return response

    except (cognito_client.exceptions.NotAuthorizedException, cognito_client.exceptions.UserNotFoundException):
        raise exceptions.INCORRECT_USERNAME_OR_PASSWORD
    except cognito_client.exceptions.UserNotConfirmedException:
        raise exceptions.USER_NOT_CONFIRMED


@router.post("/resend_activation_link")
async def resend_activation_link(user: auth_models.UserBase):
    try:
        response = await boto3_utils.resend_confirmation_code_cognito_async(
            client_id=boto3_utils.get_cognito_credentials()['COGNITO_CLIENT_ID'],
            username=user.email
        )
        return {"message": "Activation link sent", "response": response}
    except Exception as e:
        logging.error(f"Error: {str(e)}")
        raise exceptions.USER_CODE_400


@router.post('/forgot-password')
async def forgot_password(user: auth_models.UserBase):
    try:
        response = await boto3_utils.forgot_password_cognito_async(
            client_id=boto3_utils.get_cognito_credentials()['COGNITO_CLIENT_ID'],
            username=user.email
        )
        return {"message": "Password reset code sent", "response": response}
    except Exception as e:
        logging.error(f"Error: {str(e)}")
        raise exceptions.USER_CODE_400


@router.post('/confirm-forgot-password')
async def confirm_forgot_password(forgot_pass_model: auth_models.ConfirmForgotPasswordRequest):
    try:
        response = await boto3_utils.confirm_forgot_password_cognito_async(
            client_id=boto3_utils.get_cognito_credentials()['COGNITO_CLIENT_ID'],
            username=forgot_pass_model.username,
            confirmation_code=forgot_pass_model.confirmation_code,
            password=forgot_pass_model.password
        )
        return {"message": "Password changed successfully", "response": response}
    except Exception as e:
        logging.error(f"Error: {str(e)}")
        raise exceptions.USER_CODE_400


@router.post('/change-password')
async def change_password(
        change_model: auth_models.ChangePasswordRequest,
        _: auth_models.User = Depends(get_current_user)
):
    cognito_client = boto3.client("cognito-idp", region_name=boto3_utils.get_cognito_credentials()['COGNITO_REGION'])
    try:
        response = await boto3_utils.change_password_cognito_async(
            access_token=change_model.token,
            previous_password=change_model.previous_password,
            proposed_password=change_model.proposed_password
        )
        return {"message": "Password changed successfully", "response": response}
    except cognito_client.exceptions.NotAuthorizedException:
        raise exceptions.INVALID_TOKEN_OR_PASSWORD
    except cognito_client.exceptions.InvalidParameterException:
        raise exceptions.INVALID_PARAMETERS
    except Exception as e:
        logging.error(f"Error: {str(e)}")
        raise exceptions.USER_CODE_400
