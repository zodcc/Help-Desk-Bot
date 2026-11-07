from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.keyboards import main_menu_kb
from bot.services.user_service import get_or_create_user

router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message, session: AsyncSession) -> None:
    # Сохраняем пользователя в базу (или достаем, если он уже есть)
    await get_or_create_user(session, message.from_user)
    
    # Отправляем приветствие и показываем меню
    await message.answer(
        f"Здравствуйте, {message.from_user.first_name}!\n\n"
        "Я — <b>HelpDeskBot</b>. Помогу записаться на занятие "
        "или ответить на ваши вопросы.\n\n"
        "Выберите действие в меню ниже 👇",
        reply_markup=main_menu_kb()
    )