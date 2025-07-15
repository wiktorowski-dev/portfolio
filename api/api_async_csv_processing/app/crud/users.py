from sqlalchemy import select
from app.models.user import User


async def get_user_by_email(session_factory, email: str):
    async with session_factory() as session:
        stmt = select(User).where(User.email == email)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()


async def create_user(session_factory, email: str, password_hash: str):
    async with session_factory() as session:
        user = User(email=email, password_hash=password_hash)
        session.add(user)
        await session.commit()
        return user

