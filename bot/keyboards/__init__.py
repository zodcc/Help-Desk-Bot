from datetime import date
from aiogram.types import (
    InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup,
)

# Русские названия месяцев и дней для красоты
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

def dates_kb(dates: list[date]) -> InlineKeyboardMarkup:
    """Клавиатура для выбора даты."""
    rows = []
    for d in dates:
        # Красиво форматируем: "Пн, 12 ноя"
        text = f"{WEEKDAYS[d.weekday()]}, {d.day} {MONTHS[d.month - 1]}"
        rows.append([InlineKeyboardButton(text=text, callback_data=f"date:{d.isoformat()}")])
    
    rows.append([InlineKeyboardButton(text="❌ Отмена", callback_data="booking:cancel")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

def slots_kb(slots) -> InlineKeyboardMarkup:
    """Клавиатура для выбора времени (по 3 кнопки в ряд)."""
    rows, row = [], []
    for s in slots:
        row.append(InlineKeyboardButton(text=s.time.strftime("%H:%M"), callback_data=f"slot:{s.id}"))
        if len(row) == 3:
            rows.append(row)
            row = []
    if row:
        rows.append(row) # Добавляем остаток
        
    rows.append([InlineKeyboardButton(text="❌ Отмена", callback_data="booking:cancel")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

def confirm_kb() -> InlineKeyboardMarkup:
    """Клавиатура для финального подтверждения."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Подтвердить", callback_data="booking:confirm")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="booking:cancel")]
    ])