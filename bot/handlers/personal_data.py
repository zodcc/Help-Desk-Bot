from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database.models import User, Booking, BookingStatus
from bot.services.user_service import get_or_create_user

router = Router()

@router.message(F.text == "🧹 Удалить мои данные")
async def delete_personal_data(message: Message, state: FSMContext, session: AsyncSession) -> None:
    await state.clear()
    user = await get_or_create_user(session, message.from_user)

    # 1. Анонимизируем пользователя (очищаем личные данные)
    user.full_name = "Анонимный пользователь"
    user.phone = None
    user.username = None
    user.consent_given = False
    
    # 2. Отменяем все его активные записи
    await session.execute(
        update(Booking)
        .where(Booking.user_id == user.id, Booking.status == BookingStatus.CONFIRMED)
        .values(status=BookingStatus.CANCELLED)
    )
    
    await session.commit()
    
    await message.answer(
        "🧹 <b>Ваши персональные данные удалены.</b>\n\n"
        "Мы стерли ваше имя и номер телефона из нашей базы, а также отменили все активные записи."
    )