from datetime import date as date_type, timedelta
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from bot.database.models import Booking, BookingStatus, Slot

async def get_available_dates(session: AsyncSession, days: int = 7) -> list[date_type]:
    today = date_type.today()
    result = await session.execute(
        select(Slot.date)
        .where(
            Slot.date > today,
            Slot.date <= today + timedelta(days=days),
            Slot.is_booked.is_(False)
        )
        .distinct()
        .order_by(Slot.date)
    )
    return [row[0] for row in result.all()]

async def get_free_slots_for_date(session: AsyncSession, d: date_type) -> list[Slot]:
    result = await session.execute(
        select(Slot)
        .where(Slot.date == d, Slot.is_booked.is_(False))
        .order_by(Slot.time)
    )
    return list(result.scalars())

async def book_slot(session: AsyncSession, user_id: int, slot_id: int) -> Booking | None:
    result = await session.execute(
        update(Slot)
        .where(Slot.id == slot_id, Slot.is_booked.is_(False))
        .values(is_booked=True)
    )
    if result.rowcount == 0:
        return None 

    booking = Booking(user_id=user_id, slot_id=slot_id, status=BookingStatus.CONFIRMED)
    session.add(booking)
    await session.commit()
    await session.refresh(booking)
    return booking

# --- НОВЫЕ ФУНКЦИИ ДЛЯ КЛИЕНТА ---

async def get_user_bookings(session: AsyncSession, user_id: int) -> list[Booking]:
    """Получает все активные записи пользователя."""
    result = await session.execute(
        select(Booking)
        .options(joinedload(Booking.slot))
        .where(Booking.user_id == user_id, Booking.status == BookingStatus.CONFIRMED)
        .order_by(Booking.slot_id)
    )
    return list(result.scalars().all())

async def cancel_client_booking(session: AsyncSession, booking_id: int, user_id: int) -> bool:
    """Отменяет запись клиента и освобождает слот."""
    booking = await session.get(Booking, booking_id)
    # Проверяем, что запись принадлежит этому пользователю и она активна
    if booking and booking.user_id == user_id and booking.status == BookingStatus.CONFIRMED:
        booking.status = BookingStatus.CANCELLED
        slot = await session.get(Slot, booking.slot_id)
        if slot:
            slot.is_booked = False
        await session.commit()
        return True
    return False