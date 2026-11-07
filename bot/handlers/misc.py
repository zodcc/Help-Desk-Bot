from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

router = Router()

@router.message(F.text == "👤 Связаться с оператором")
async def stub_operator(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("🚧 Функция «Связаться с оператором» появится на Этапе 3.")

@router.message(F.text == "🧹 Удалить мои данные")
async def stub_delete(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("🚧 Функция удаления данных появится на Этапе 4.")