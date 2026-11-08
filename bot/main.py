import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from bot.config import settings
from bot.middlewares.db import DBSessionMiddleware
# Импортируем все наши обработчики, включая operator
from bot.handlers import start, faq, booking, misc, operator

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

    # Подключаем middleware (базу данных)
    dp.update.middleware(DBSessionMiddleware())

    # Подключаем роутеры (порядок очень важен!)
    dp.include_router(start.router)
    dp.include_router(booking.router)
    dp.include_router(misc.router)
    dp.include_router(operator.router)  # <-- ВОТ ОН
    dp.include_router(faq.router)       # faq всегда идет последним

    await bot.delete_webhook(drop_pending_updates=True)
    logging.info("HelpDeskBot запущен! (Этап 3 в процессе)")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Бот остановлен.")