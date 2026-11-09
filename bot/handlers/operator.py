import re
from aiogram import F, Router
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from bot.config import settings
from bot.database.models import User, Dialog, DialogStatus
from bot.keyboards import main_menu_kb
from bot.services.operator_service import create_dialog, save_message, get_active_dialog
from bot.services.user_service import get_or_create_user

router = Router()

# ==========================================
# ЧАСТЬ 1: КЛИЕНТ
# ==========================================

@router.message(F.text == "👤 Связаться с оператором")
async def start_dialog(message: Message, state: FSMContext, session: AsyncSession) -> None:
    user = await get_or_create_user(session, message.from_user)
    dialog = await create_dialog(session, user.id)
    
    await state.set_state("in_dialog")
    await state.update_data(dialog_id=dialog.id)
    
    await message.answer("Вы подключены к оператору. Напишите ваш вопрос, и мы ответим вам здесь.")
    
    if settings.OPERATOR_CHAT_ID:
        await message.bot.send_message(
            chat_id=settings.OPERATOR_CHAT_ID,
            text=f"🆘 <b>Новый диалог #{dialog.id}</b>\n"
                 f"Клиент: {user.full_name} (@{user.username})\n\n"
                 f"<i>Чтобы ответить, сделайте Reply на это сообщение.\nЧтобы закрыть диалог, напишите /close (реплаем).</i>"
        )

@router.message(F.text, StateFilter("in_dialog"))
async def client_message(message: Message, state: FSMContext, session: AsyncSession) -> None:
    data = await state.get_data()
    dialog_id = data.get("dialog_id")
    
    # Проверяем, не закрыт ли уже диалог
    result = await session.execute(select(Dialog.status).where(Dialog.id == dialog_id))
    status = result.scalar_one_or_none()

    if status == DialogStatus.CLOSED:
        await state.clear()
        await message.answer("Этот диалог уже завершен. Возвращаю вас в главное меню.", reply_markup=main_menu_kb())
        return
    
    user = await get_or_create_user(session, message.from_user)
    await save_message(session, dialog_id, "client", message.text)
    
    if settings.OPERATOR_CHAT_ID:
        await message.bot.send_message(
            chat_id=settings.OPERATOR_CHAT_ID,
            text=f"💬 <b>Диалог #{dialog_id}</b> | {user.full_name}:\n{message.text}"
        )


# ==========================================
# ЧАСТЬ 2: ОПЕРАТОР
# ==========================================

@router.message(F.chat.id == settings.OPERATOR_CHAT_ID, Command("close"), F.reply_to_message)
async def close_dialog(message: Message, session: AsyncSession) -> None:
    original_text = message.reply_to_message.text or ""
    match = re.search(r"Диалог #(\d+)", original_text)
    
    if not match:
        await message.reply("⚠️ Сделайте Reply (ответ) на сообщение бота с ID диалога, чтобы закрыть его.")
        return

    dialog_id = int(match.group(1))
    
    # Закрываем в базе
    dialog = await session.get(Dialog, dialog_id)
    if dialog:
        dialog.status = DialogStatus.CLOSED
        await session.commit()
        
        # Уведомляем клиента
        result = await session.execute(select(User.tg_id).where(User.id == dialog.user_id))
        client_tg_id = result.scalar_one_or_none()
        
        if client_tg_id:
            await message.bot.send_message(
                chat_id=client_tg_id,
                text="Оператор завершил диалог. Если у вас остались вопросы, вы можете задать их снова.",
                reply_markup=main_menu_kb()
            )
        await message.reply(f"✅ Диалог #{dialog_id} закрыт.")
    else:
        await message.reply("⚠️ Диалог не найден в базе.")

@router.message(F.chat.id == settings.OPERATOR_CHAT_ID, F.reply_to_message, F.text)
async def operator_reply(message: Message, session: AsyncSession) -> None:
    original_text = message.reply_to_message.text or ""
    match = re.search(r"Диалог #(\d+)", original_text)
    
    if not match:
        await message.reply("⚠️ Не могу найти ID диалога. Сделайте Reply на сообщение бота.")
        return

    dialog_id = int(match.group(1))
    
    result = await session.execute(
        select(User.tg_id).join(Dialog, Dialog.user_id == User.id).where(Dialog.id == dialog_id)
    )
    client_tg_id = result.scalar_one_or_none()

    if not client_tg_id:
        await message.reply("⚠️ Клиент не найден.")
        return

    try:
        await message.bot.send_message(
            chat_id=client_tg_id,
            text=f"👨‍💻 <b>Оператор:</b>\n{message.text}"
        )
        await save_message(session, dialog_id, "operator", message.text)
        await message.react([{"type": "emoji", "emoji": "👍"}])
    except Exception as e:
        await message.reply(f"❌ Ошибка отправки: {e}")