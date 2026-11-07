from datetime import datetime
from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.keyboards import confirm_kb, dates_kb, main_menu_kb, slots_kb
from bot.services.booking_service import book_slot, get_available_dates, get_free_slots_for_date
from bot.services.user_service import get_or_create_user
from bot.states import BookingSG

router = Router()

# Команда для отмены на любом шаге
@router.message(Command("cancel"))
async def cancel_cmd(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("Действие отменено.", reply_markup=main_menu_kb())

# === ШАГ 1: Вход в сценарий ===
@router.message(F.text == "📅 Записаться на занятие")
async def start_booking(message: Message, state: FSMContext, session: AsyncSession) -> None:
    await state.clear()
    dates = await get_available_dates(session)
    
    if not dates:
        await message.answer("Пока нет свободных слотов. Попробуйте позже.")
        return
        
    await state.set_state(BookingSG.choose_date)
    await message.answer("Выберите удобную дату:", reply_markup=dates_kb(dates))

# === ШАГ 2: Выбор даты ===
@router.callback_query(BookingSG.choose_date, F.data.startswith("date:"))
async def choose_date(call: CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    iso_date = call.data.split(":")[1]
    d = datetime.fromisoformat(iso_date).date()
    
    slots = await get_free_slots_for_date(session, d)
    if not slots:
        await call.answer("На эту дату слоты закончились", show_alert=True)
        dates = await get_available_dates(session)
        await call.message.edit_text("Выберите другую дату:", reply_markup=dates_kb(dates))
        return

    await state.update_data(slot_date=iso_date)
    await state.set_state(BookingSG.choose_slot)
    await call.message.edit_text(f"Свободное время на {d.strftime('%d.%m.%Y')}:", reply_markup=slots_kb(slots))
    await call.answer()

# === ШАГ 3: Выбор времени ===
@router.callback_query(BookingSG.choose_slot, F.data.startswith("slot:"))
async def choose_slot(call: CallbackQuery, state: FSMContext) -> None:
    slot_id = int(call.data.split(":")[1])
    await state.update_data(slot_id=slot_id)
    await state.set_state(BookingSG.enter_name)
    await call.message.edit_text("Введите ваше имя (как к вам обращаться?):")
    await call.answer()

# === ШАГ 4: Ввод имени ===
@router.message(BookingSG.enter_name, F.text)
async def enter_name(message: Message, state: FSMContext) -> None:
    name = message.text.strip()
    if len(name) < 2:
        await message.answer("Слишком коротко. Введите имя ещё раз:")
        return
    await state.update_data(full_name=name)
    await state.set_state(BookingSG.enter_phone)
    await message.answer("Введите номер телефона (например, +79991234567):")

# === ШАГ 5: Ввод телефона ===
@router.message(BookingSG.enter_phone, F.text)
async def enter_phone(message: Message, state: FSMContext) -> None:
    raw = message.text.strip()
    digits = "".join(ch for ch in raw if ch.isdigit())
    
    if not (10 <= len(digits) <= 15):
        await message.answer("Неверный номер. Попробуйте ещё раз:")
        return

    await state.update_data(phone=raw)
    data = await state.get_data()
    await state.set_state(BookingSG.confirm)
    
    await message.answer(
        "Проверьте данные записи:\n\n"
        f"📅 Дата: <b>{data['slot_date']}</b>\n"
        f"👤 Имя: <b>{data['full_name']}</b>\n"
        f"📞 Телефон: <b>{raw}</b>\n\n"
        "Всё верно?",
        reply_markup=confirm_kb()
    )

# === ШАГ 6: Подтверждение и сохранение ===
@router.callback_query(BookingSG.confirm, F.data == "booking:confirm")
async def confirm_booking(call: CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    data = await state.get_data()
    
    # Обновляем данные пользователя в базе (имя и телефон)
    user = await get_or_create_user(session, call.from_user)
    user.full_name = data["full_name"]
    user.phone = data["phone"]
    user.consent_given = True
    await session.commit()

    # Бронируем слот
    booking = await book_slot(session, user.id, data["slot_id"])
    await state.clear()

    if booking is None:
        await call.message.edit_text("😔 Этот слот только что заняли. Попробуйте выбрать другой.")
    else:
        await call.message.edit_text(
            f"✅ <b>Запись подтверждена!</b>\n\n"
            f"📅 {data['slot_date']}\n"
            f"👤 {data['full_name']}\n"
            f"📞 {data['phone']}\n\n"
            "Ждём вас!"
        )
    await call.answer()

# === Отмена на любом шаге ===
@router.callback_query(F.data == "booking:cancel")
async def cancel_booking(call: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await call.message.edit_text("Запись отменена.")
    await call.answer()