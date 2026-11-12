from datetime import date
from aiogram.types import (
    InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup,
)

WEEKDAYS = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
MONTHS = ["янв", "фев", "мар", "апр", "мая", "июн", "июл", "авг", "сен", "окт", "ноя", "дек"]

def main_menu_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📅 Записаться на занятие")],
            [KeyboardButton(text="📋 Мои записи")], # <-- Новая кнопка
            [KeyboardButton(text="❓ Задать вопрос")],
            [KeyboardButton(text="👤 Связаться с оператором")],
            [KeyboardButton(text="🧹 Удалить мои данные")],
        ],
        resize_keyboard=True,
        input_field_placeholder="Выберите действие в меню..."
    )

def my_bookings_kb(bookings) -> InlineKeyboardMarkup:
    """Клавиатура со списком записей пользователя для отмены."""
    rows = []
    for b in bookings:
        date_str = b.slot.date.strftime("%d.%m")
        time_str = b.slot.time.strftime("%H:%M")
        rows.append([InlineKeyboardButton(
            text=f"❌ Отменить {date_str} в {time_str}", 
            callback_data=f"client_cancel:{b.id}"
        )])
    rows.append([InlineKeyboardButton(text="🏠 В главное меню", callback_data="booking:cancel")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

# ... (остальные функции dates_kb, slots_kb, name_kb, phone_reply_kb, confirm_kb остаются без изменений)

def dates_kb(dates: list[date]) -> InlineKeyboardMarkup:
    rows = []
    for d in dates:
        text = f"{WEEKDAYS[d.weekday()]}, {d.day} {MONTHS[d.month - 1]}"
        rows.append([InlineKeyboardButton(text=text, callback_data=f"date:{d.isoformat()}")])
    
    rows.append([InlineKeyboardButton(text="🏠 В главное меню", callback_data="booking:cancel")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

def slots_kb(slots) -> InlineKeyboardMarkup:
    rows, row = [], []
    for s in slots:
        row.append(InlineKeyboardButton(text=s.time.strftime("%H:%M"), callback_data=f"slot:{s.id}"))
        if len(row) == 3:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
        
    rows.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="booking:back_to_dates")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

def name_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="⬅️ Назад", callback_data="booking:back_to_slots"),
            InlineKeyboardButton(text="🏠 В главное меню", callback_data="booking:cancel")
        ]
    ])

def phone_reply_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📱 Поделиться контактом", request_contact=True)],
            [KeyboardButton(text="⬅️ Назад"), KeyboardButton(text="🏠 В главное меню")]
        ],
        resize_keyboard=True,
        one_time_keyboard=False
    )

def confirm_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Подтвердить", callback_data="booking:confirm")],
        [
            InlineKeyboardButton(text="⬅️ Назад", callback_data="booking:back_to_phone"),
            InlineKeyboardButton(text="🏠 В главное меню", callback_data="booking:cancel")
        ]
    ])