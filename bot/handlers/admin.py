from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from bot.config import settings
from bot.database.models import User, Booking

router = Router()

# Фильтр F.from_user.id.in_(settings.admin_ids) защищает команду от обычных юзеров
@router.message(Command("stats"), F.from_user.id.in_(settings.admin_ids))
async def cmd_stats(message: Message, session: AsyncSession) -> None:
    # Считаем пользователей
    users_count = await session.scalar(select(func.count()).select_from(User))
    # Считаем записи
    bookings_count = await session.scalar(select(func.count()).select_from(Booking))

    await message.answer(
        f"📊 <b>Статистика HelpDeskBot</b>\n\n"
        f"👥 Всего пользователей: <b>{users_count}</b>\n"
        f"📅 Всего записей: <b>{bookings_count}</b>"
    )