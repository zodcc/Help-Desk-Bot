import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from bot.config import settings
from bot.middlewares.db import DBSessionMiddleware
from bot.handlers import start, faq, booking, misc

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

    # Подключаем БД ко всем сообщениям
    dp.update.middleware(DBSessionMiddleware())

    # Подключаем роутеры (обработчики) в строгом порядке
    dp.include_router(start.router)
    dp.include_router(booking.router)
    dp.include_router(misc.router)
    dp.include_router(faq.router) # faq идет предпоследним (ловит остальной текст)

    await bot.delete_webhook(drop_pending_updates=True)
    logging.info("HelpDeskBot запущен! (Этап 2 готов)")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Бот остановлен.")