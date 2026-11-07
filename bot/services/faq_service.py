from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database.models import FAQ


async def find_answer(session: AsyncSession, text: str) -> str | None:
    """
    Ищет ответ на вопрос в базе данных.
    Проходит по всем записям в таблице FAQ, разбивает ключевые слова по запятой
    и проверяет, есть ли хотя бы одно из них в сообщении пользователя.
    """
    # Приводим текст пользователя к нижнему регистру для удобства поиска
    text_lower = text.lower()
    
    # Запрашиваем все вопросы из базы
    result = await session.execute(select(FAQ))
    
    for item in result.scalars():
        # Разбиваем строку "цена,стоимость,сколько стоит" на список слов
        keywords = (k.strip().lower() for k in item.keywords.split(",") if k.strip())
        
        for kw in keywords:
            if kw in text_lower:
                return item.answer  # Возвращаем первый найденный ответ
                
    return None  # Если ничего не нашли, возвращаем пустоту