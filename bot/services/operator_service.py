from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database.models import Dialog, DialogStatus, Message

async def get_active_dialog(session: AsyncSession, user_id: int) -> Dialog | None:
    """Ищет открытый диалог у пользователя."""
    result = await session.execute(
        select(Dialog).where(Dialog.user_id == user_id, Dialog.status == DialogStatus.OPEN)
    )
    return result.scalar_one_or_none()

async def create_dialog(session: AsyncSession, user_id: int) -> Dialog:
    """Создает новый диалог, если его нет."""
    dialog = await get_active_dialog(session, user_id)
    if dialog:
        return dialog
        
    dialog = Dialog(user_id=user_id, status=DialogStatus.OPEN)
    session.add(dialog)
    await session.commit()
    await session.refresh(dialog)
    return dialog

async def save_message(session: AsyncSession, dialog_id: int, sender_type: str, text: str) -> None:
    """Сохраняет сообщение в историю (sender_type: 'client' или 'operator')."""
    msg = Message(dialog_id=dialog_id, sender_type=sender_type, text=text)
    session.add(msg)
    await session.commit()