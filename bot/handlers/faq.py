from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.services.faq_service import find_answer

router = Router()

# 1. Обработчик нажатия на кнопку "Задать вопрос"
@router.message(F.text == "❓ Задать вопрос")
async def ask_question(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("Напишите ваш вопрос одним сообщением — я постараюсь найти ответ в базе знаний.")

# 2. Обработчик любого текста (сработает, если текст не начинается с "/")
@router.message(F.text, ~F.text.startswith("/"))
async def answer_faq(message: Message, session: AsyncSession) -> None:
    # Защита: если пользователь нажал другие кнопки меню, мы не ищем их в FAQ
    ignore_buttons = [
        "📅 Записаться на занятие", 
        "👤 Связаться с оператором", 
        "🧹 Удалить мои данные"
    ]
    if message.text in ignore_buttons:
        return

    # Ищем ответ в базе данных
    answer = await find_answer(session, message.text)
    
    if answer:
        await message.answer(answer)
    else:
        await message.answer(
            "К сожалению, ответа в базе знаний нет 🤔\n\n"
            "Нажмите «👤 Связаться с оператором» — я передам вопрос сотруднику."
        )