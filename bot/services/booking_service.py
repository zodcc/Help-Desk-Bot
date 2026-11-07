from datetime import date as date_type, timedelta
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from bot.database.models import Booking, BookingStatus, Slot

async def get_available_dates(session: AsyncSession, days: int = 7) -> list[date_type]:
    """Возвращает список уникальных дат на 7 дней вперед, где есть свободные слоты."""
    today = date_type.today()
    result = await session.execute(
        select(Slot.date)
        .where(
            Slot.date > today, # Начиная с завтрашнего дня
            Slot.date <= today + timedelta(days=days),
            Slot.is_booked.is_(False) # Только те, где есть свободное время
        )
        .distinct()
        .order_by(Slot.date)
    )
    return [row[0] for row in result.all()]

async def get_free_slots_for_date(session: AsyncSession, d: date_type) -> list[Slot]:
    """Возвращает список свободных слотов на конкретную дату."""
    result = await session.execute(
        select(Slot)
        .where(Slot.date == d, Slot.is_booked.is_(False))
        .order_by(Slot.time)
    )
    return list(result.scalars())

async def book_slot(session: AsyncSession, user_id: int, slot_id: int) -> Booking | None:
    """
    Бронирует слот. Использует атомарный UPDATE на уровне базы данных.
    Это защищает от ситуации, когда два человека одновременно жмут на одно время.
    """
    # Пытаемся обновить слот, ТОЛЬКО если он еще не занят (is_booked == False)
    result = await session.execute(
        update(Slot)
        .where(Slot.id == slot_id, Slot.is_booked.is_(False))
        .values(is_booked=True)
    )
    
    # Если база данных обновила 0 строк, значит слот уже кто-то перехватил
    if result.rowcount == 0:
        return None 

    # Создаем запись о бронировании в таблице bookings
    booking = Booking(user_id=user_id, slot_id=slot_id, status=BookingStatus.CONFIRMED)
    session.add(booking)
    await session.commit()
    await session.refresh(booking)
    return booking