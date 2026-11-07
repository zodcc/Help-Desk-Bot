import asyncio
import logging

from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import Message

from bot.config import settings

# Настраиваем логи, чтобы видеть в терминале, что происходит
logging.basicConfig(
    level=settings.LOG_LEVEL,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

async def main() -> None:
    # Инициализируем бота (берем токен из config.py) и включаем HTML-разметку
    bot = Bot(
        token=settings.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher()

    # Простейший обработчик: реагирует на любой текст
    @dp.message(F.text)
    async def echo_handler(message: Message) -> None:
        await message.answer(
            f"🛠 <b>Связка работает!</b>\n\n"
            f"Твой Telegram ID: <code>{message.from_user.id}</code>\n"
            f"Текст сообщения: <i>{message.text}</i>"
        )

    # Очищаем старые зависшие обновления и запускаем бота
    await bot.delete_webhook(drop_pending_updates=True)
    logging.info("HelpDeskBot запущен! (Эхо-режим)")
    
    # Запускаем бесконечный цикл прослушивания
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Бот остановлен.")