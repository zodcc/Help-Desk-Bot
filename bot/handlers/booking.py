from datetime import datetime
from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.keyboards import confirm_kb, dates_kb, main_menu_kb, slots_kb, back_text_kb
from bot.services.booking_service import book_slot, get_available_dates, get_free_slots_for_date
from bot.services.user_service import get_or_create_user
from bot.states import BookingSG

router = Router()

@router.message(Command("cancel"))
async def cancel_cmd(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("Действие отменено.", reply_markup=main_menu_kb())

@router.message(F.text == "📅 Записаться на занятие")
async def start_booking(message: Message, state: FSMContext, session: AsyncSession) -> None:
    await state.clear()
    dates = await get_available_dates(session)
    
    if not dates:
        await message.answer("Пока нет свободных слотов. Попробуйте позже.", reply_markup=main_menu_kb())
        return
        
    await state.set_state(BookingSG.choose_date)
    await message.answer("Выберите удобную дату:", reply_markup=dates_kb(dates))

# Обработка текстовой кнопки "Назад" при выборе даты (возврат в меню)
@router.message(BookingSG.choose_date, F.text == "⬅️ Назад")
async def back_from_dates_text(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("Вы вернулись в главное меню.", reply_markup=main_menu_kb())

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

# Обработка текстовой кнопки "Назад" при выборе времени (возврат к датам)
@router.message(BookingSG.choose_slot, F.text == "⬅️ Назад")
async def back_from_slots_text(message: Message, state: FSMContext, session: AsyncSession) -> None:
    dates = await get_available_dates(session)
    await state.set_state(BookingSG.choose_date)
    await message.answer("Выберите удобную дату:", reply_markup=dates_kb(dates))

@router.callback_query(F.data == "booking:back_to_dates")
async def back_to_dates(call: CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    dates = await get_available_dates(session)
    await state.set_state(BookingSG.choose_date)
    await call.message.edit_text("Выберите удобную дату:", reply_markup=dates_kb(dates))
    await call.answer()

@router.callback_query(BookingSG.choose_slot, F.data.startswith("slot:"))
async def choose_slot(call: CallbackQuery, state: FSMContext) -> None:
    slot_id = int(call.data.split(":")[1])
    await state.update_data(slot_id=slot_id)
    await state.set_state(BookingSG.enter_name)
    
    # Отправляем новое сообщение (не edit), так как нужна Reply-клавиатура
    await call.message.answer("Введите ваше имя (как к вам обращаться?):", reply_markup=back_text_kb())
    await call.message.delete()
    await call.answer()

@router.message(BookingSG.enter_name, F.text)
async def enter_name(message: Message, state: FSMContext, session: AsyncSession) -> None:
    if message.text == "⬅️ Назад":
        data = await state.get_data()
        d = datetime.fromisoformat(data['slot_date']).date()
        slots = await get_free_slots_for_date(session, d)
        await state.set_state(BookingSG.choose_slot)
        await message.answer(f"Свободное время на {d.strftime('%d.%m.%Y')}:", reply_markup=slots_kb(slots))
        return

    name = message.text.strip()
    if len(name) < 2:
        await message.answer("Слишком коротко. Введите имя ещё раз:", reply_markup=back_text_kb())
        return
        
    await state.update_data(full_name=name)
    await state.set_state(BookingSG.enter_phone)
    await message.answer("Введите номер телефона (например, +79991234567):", reply_markup=back_text_kb())

@router.message(BookingSG.enter_phone, F.text)
async def enter_phone(message: Message, state: FSMContext) -> None:
    if message.text == "⬅️ Назад":
        await state.set_state(BookingSG.enter_name)
        await message.answer("Введите ваше имя (как к вам обращаться?):", reply_markup=back_text_kb())
        return

    raw = message.text.strip()
    digits = "".join(ch for ch in raw if ch.isdigit())
    
    if not (10 <= len(digits) <= 15):
        await message.answer("Неверный номер. Попробуйте ещё раз:", reply_markup=back_text_kb())
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

@router.callback_query(F.data == "booking:back_to_phone")
async def back_to_phone(call: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(BookingSG.enter_phone)
    await call.message.answer("Введите номер телефона (например, +79991234567):", reply_markup=back_text_kb())
    await call.message.delete()
    await call.answer()

@router.callback_query(BookingSG.confirm, F.data == "booking:confirm")
async def confirm_booking(call: CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    data = await state.get_data()
    
    user = await get_or_create_user(session, call.from_user)
    user.full_name = data["full_name"]
    user.phone = data["phone"]
    user.consent_given = True
    await session.commit()

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

@router.callback_query(F.data == "booking:cancel")
async def cancel_booking(call: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await call.message.delete()
    await call.message.answer("Вы вернулись в главное меню.", reply_markup=main_menu_kb())
    await call.answer()