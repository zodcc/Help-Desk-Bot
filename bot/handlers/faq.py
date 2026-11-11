from aiogram import F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.services.faq_service import find_answer

router = Router()

@router.message(F.text == "❓ Задать вопрос")
async def ask_question(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("Напишите ваш вопрос одним сообщением — я постараюсь найти ответ в базе знаний.")

@router.message(StateFilter(None), F.text, ~F.text.startswith("/"))
async def answer_faq(message: Message, session: AsyncSession) -> None:
    # Игнорируем кнопки меню и кнопку "Назад"
    ignore_buttons = [
        "📅 Записаться на занятие", 
        "👤 Связаться с оператором", 
        "🧹 Удалить мои данные",
        "⬅️ Назад",
        "🏠 В главное меню"
    ]
    if message.text in ignore_buttons:
        return

    answer = await find_answer(session, message.text)
    if answer:
        await message.answer(answer)
    else:
        await message.answer(
            "К сожалению, ответа в базе знаний нет 🤔\n\n"
            "Нажмите «👤 Связаться с оператором» — я передам вопрос сотруднику."
        )