import os
import uuid

from app.utils.sql_connection import fetch_one_dict, cursor_wrapper
from app.models import auth as auth_model


@cursor_wrapper
async def get_user_by_email(email: str, cursor=None) -> auth_model.UserId | None:
    query = f'SELECT id, email FROM {os.environ["SQL_SCHEMA"]}.users WHERE email = %s'
    await cursor.execute(query, (email,))

    fetch = await cursor.fetchone()
    if not fetch:
        return None

    return auth_model.UserId(**fetch_one_dict(cursor, fetch_result=fetch))


@cursor_wrapper
async def get_user_by_id(id_: str, cursor=None) -> auth_model.User | None:
    query = f'''
    SELECT 
        u.id as user_id, u.email, s.*
    FROM {os.environ["SQL_SCHEMA"]}.users u
    INNER JOIN {os.environ["SQL_SCHEMA"]}.account_settings s
    ON u.id = s.user_id 
    WHERE u.id = %s
    '''
    await cursor.execute(query, (id_,))

    fetch = await cursor.fetchone()
    if not fetch:
        return None

    data = fetch_one_dict(cursor, fetch_result=fetch)
    return auth_model.User(
        id=data['user_id'],
        email=data['email'],
        account_settings=auth_model.AccountSettingsDB(
            **{k: v for k, v in data.items() if k not in ('email',)}
        )
    )


@cursor_wrapper
async def create_user(user_id: str, user_email: str, newsletter_subscribed: bool, cursor=None):
    db_user = auth_model.User(
        id=user_id,
        email=user_email,
        account_settings=auth_model.AccountSettingsDB(
            user_id=user_id,
            newsletter_subscribed=newsletter_subscribed
        )
    )

    query = f'INSERT INTO {os.environ["SQL_SCHEMA"]}.users (id, email) VALUES (%s, %s)'
    await cursor.execute(query, (db_user.id, db_user.email))


@cursor_wrapper
async def delete_user_by_id(id_: str, cursor=None):
    query = f'DELETE FROM {os.environ["SQL_SCHEMA"]}.users WHERE id = %s'
    await cursor.execute(query, (id_,))
