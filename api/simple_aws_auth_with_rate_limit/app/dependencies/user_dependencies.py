from app.models import auth
from app.crud import user as user_crud


async def get_user_db_create_if_not_exists(user: auth.UserId) -> auth.UserId:
    user_sql_resp = await user_crud.get_user_by_email(user.email)
    if not user_sql_resp:
        # Creating user if not exists in DB
        await user_crud.create_user(user_id=user.id, user_email=user.email, newsletter_subscribed=False)

        return await get_user_db_create_if_not_exists(user)

    return user_sql_resp
