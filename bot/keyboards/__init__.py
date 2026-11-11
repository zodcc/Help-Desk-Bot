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
            [KeyboardButton(text="❓ Задать вопрос")],
            [KeyboardButton(text="👤 Связаться с оператором")],
            [KeyboardButton(text="🧹 Удалить мои данные")],
        ],
        resize_keyboard=True,
        input_field_placeholder="Выберите действие в меню..."
    )

def back_text_kb() -> ReplyKeyboardMarkup:
    """Клавиатура с одной кнопкой Назад (для ввода текста)"""
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="⬅️ Назад")]],
        resize_keyboard=True
    )

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

def confirm_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Подтвердить", callback_data="booking:confirm")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="booking:back_to_phone")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="booking:cancel")]
    ])