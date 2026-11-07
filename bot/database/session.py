from sqlalchemy.ext.asyncio import (
    AsyncSession, async_sessionmaker, create_async_engine,
)

from bot.config import settings

# Создаём асинхронный движок. echo=False означает, что SQL-запросы не будут 
# выводиться в консоль (если захочешь посмотреть, как SQLAlchemy работает под капотом, поставь True).
engine = create_async_engine(settings.DATABASE_URL, echo=False, future=True)

# Фабрика сессий. Каждый раз, когда нужно обратиться к БД, мы будем открывать новую сессию.
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)