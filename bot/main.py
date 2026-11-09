import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from bot.config import settings
from bot.middlewares.db import DBSessionMiddleware
# Импортируем все наши обработчики (misc удален)
from bot.handlers import start, faq, booking, operator, personal_data, admin

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

async def main() -> None:
    bot = Bot(
        token=settings.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher()

    dp.update.middleware(DBSessionMiddleware())

    # Подключаем роутеры
    dp.include_router(start.router)
    dp.include_router(booking.router)
    dp.include_router(operator.router)
    dp.include_router(personal_data.router) # <-- Добавили
    dp.include_router(admin.router)         # <-- Добавили
    dp.include_router(faq.router)           # faq всегда последним

    await bot.delete_webhook(drop_pending_updates=True)
    logging.info("HelpDeskBot запущен! (Этап 4)")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Бот остановлен.")