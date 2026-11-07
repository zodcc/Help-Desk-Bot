import asyncio
from datetime import date, time, timedelta
from sqlalchemy import select

from bot.database.models import FAQ, Slot
from bot.database.session import async_session

# Наши базовые вопросы и ответы (ключевые слова через запятую)
SEED_FAQ = [
    ("цена,стоимость,сколько стоит", "Стоимость занятия — 1500 ₽ за одно посещение."),
    ("адрес,где находитесь,как добраться", "Мы находимся по адресу: г. Санкт-Петербург, Невский пр., д. 1."),
    ("график,часы работы,когда работаете", "Мы работаем ежедневно с 09:00 до 21:00 без выходных."),
    ("отмена,перенести,отменить запись", "Перенести запись можно не позднее чем за 3 часа до начала."),
]

async def seed() -> None:
    async with async_session() as session:
        # 1. Проверяем, есть ли уже вопросы в базе. Если нет — добавляем.
        existing = await session.execute(select(FAQ.id).limit(1))
        if existing.scalar_one_or_none() is None:
            for kw, ans in SEED_FAQ:
                session.add(FAQ(keywords=kw, answer=ans))
            print(f"[seed] добавлено FAQ: {len(SEED_FAQ)}")
        else:
            print("[seed] FAQ уже есть, пропускаем.")

        # 2. Генерируем слоты на 7 дней вперёд
        today = date.today()
        slot_times = [time(10, 0), time(12, 0), time(14, 0), time(16, 0), time(18, 0)]
        created = 0
        for offset in range(1, 8): # от 1 до 7 дней
            d = today + timedelta(days=offset)
            for t in slot_times:
                # Проверяем, нет ли уже такого слота (чтобы не дублировать)
                exists = await session.execute(select(Slot.id).where(Slot.date == d, Slot.time == t))
                if exists.scalar_one_or_none() is None:
                    session.add(Slot(date=d, time=t, is_booked=False))
                    created += 1
        
        print(f"[seed] добавлено слотов: {created}")
        await session.commit()

if __name__ == "__main__":
    asyncio.run(seed())