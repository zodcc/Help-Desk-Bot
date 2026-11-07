from aiogram.types import User as TgUser
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database.models import User, UserRole

async def get_or_create_user(session: AsyncSession, tg_user: TgUser) -> User:
    """Ищет пользователя в БД. Если не находит — создает нового."""
    result = await session.execute(select(User).where(User.tg_id == tg_user.id))
    user = result.scalar_one_or_none()

    if user is None:
        user = User(
            tg_id=tg_user.id,
            username=tg_user.username,
            full_name=tg_user.full_name,
            role=UserRole.CLIENT
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        
    return user