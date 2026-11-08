import re
from aiogram import F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from bot.config import settings
from bot.database.models import User, Dialog
from bot.services.operator_service import create_dialog, save_message
from bot.services.user_service import get_or_create_user

router = Router()

# ==========================================
# ЧАСТЬ 1: КЛИЕНТ
# ==========================================

@router.message(F.text == "👤 Связаться с оператором")
async def start_dialog(message: Message, state: FSMContext, session: AsyncSession) -> None:
    print("DEBUG: Кнопка 'Связаться с оператором' нажата!")
    
    user = await get_or_create_user(session, message.from_user)
    dialog = await create_dialog(session, user.id)
    
    await state.set_state("in_dialog")
    await state.update_data(dialog_id=dialog.id)
    
    await message.answer("Вы подключены к оператору. Напишите ваш вопрос, и мы ответим вам здесь.")
    
    if settings.OPERATOR_CHAT_ID:
        try:
            await message.bot.send_message(
                chat_id=settings.OPERATOR_CHAT_ID,
                text=f"🆘 <b>Новый диалог #{dialog.id}</b>\n"
                     f"Клиент: {user.full_name} (@{user.username})\n\n"
                     f"<i>Чтобы ответить, сделайте Reply на сообщение клиента ниже.</i>"
            )
            print("DEBUG: Уведомление в группу успешно отправлено!")
        except Exception as e:
            print(f"DEBUG ОШИБКА ОТПРАВКИ В ГРУППУ: {e}")
    else:
        print("DEBUG: OPERATOR_CHAT_ID пустой в .env!")


@router.message(F.text, StateFilter("in_dialog"))
async def client_message(message: Message, state: FSMContext, session: AsyncSession) -> None:
    data = await state.get_data()
    dialog_id = data.get("dialog_id")
    
    user = await get_or_create_user(session, message.from_user)
    await save_message(session, dialog_id, "client", message.text)
    
    if settings.OPERATOR_CHAT_ID:
        await message.bot.send_message(
            chat_id=settings.OPERATOR_CHAT_ID,
            text=f"💬 <b>Диалог #{dialog_id}</b> | {user.full_name}:\n{message.text}"
        )


# ==========================================
# ЧАСТЬ 2: ОПЕРАТОР (ответы из группы)
# ==========================================

@router.message(F.chat.id == settings.OPERATOR_CHAT_ID, F.reply_to_message, F.text)
async def operator_reply(message: Message, session: AsyncSession) -> None:
    original_text = message.reply_to_message.text or ""
    
    # Ищем в тексте паттерн "Диалог #123"
    match = re.search(r"Диалог #(\d+)", original_text)
    
    if not match:
        await message.reply("⚠️ Не могу найти ID диалога в сообщении. Убедитесь, что вы делаете Reply на сообщение бота.")
        return

    dialog_id = int(match.group(1))
    
    # Находим ID клиента в базе
    result = await session.execute(
        select(User.tg_id).join(Dialog, Dialog.user_id == User.id).where(Dialog.id == dialog_id)
    )
    client_tg_id = result.scalar_one_or_none()

    if not client_tg_id:
        await message.reply("⚠️ Клиент не найден в базе.")
        return

    try:
        await message.bot.send_message(
            chat_id=client_tg_id,
            text=f"👨‍💻 <b>Оператор:</b>\n{message.text}"
        )
        await save_message(session, dialog_id, "operator", message.text)
        await message.react([{"type": "emoji", "emoji": "👍"}])
    except Exception as e:
        await message.reply(f"❌ Ошибка отправки клиенту: {e}")