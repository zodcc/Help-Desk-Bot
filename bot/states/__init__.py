from aiogram.fsm.state import State, StatesGroup

class BookingSG(StatesGroup):
    choose_date = State()   # Ждем выбора даты
    choose_slot = State()   # Ждем выбора времени
    enter_name = State()    # Ждем ввода имени
    enter_phone = State()   # Ждем ввода телефона
    confirm = State()       # Ждем подтверждения (Да/Нет)