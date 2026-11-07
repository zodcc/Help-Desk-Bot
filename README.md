# HelpDeskBot

Telegram-бот для автоматизации записи на занятия и клиентской поддержки. 
Разрабатывается в соответствии с Техническим заданием.

## 🛠 Стек технологий
- **Язык:** Python 3.14
- **Библиотека бота:** aiogram 3.x
- **База данных:** SQLite + SQLAlchemy 2.0 (async)
- **Миграции:** Alembic

## 🚀 Как запустить локально

1. Клонировать репозиторий:
   ```bash
   git clone <ссылка_на_репозиторий>
   cd Help-Desk-Bot
2. Создать виртуальное окружение и установить зависимости:
  ```bash
  python3 -m venv .venv
  source .venv/bin/activate
  pip install -r requirements.txt
  ```
3. Создать файл .env (скопировать из .env.example) и вписать свои данные:
- BOT_TOKEN — токен от @BotFather
- ADMIN_IDS — ваш Telegram ID
4. Применить миграции и заполнить базу:
  ```bash
  alembic upgrade head
  python -m scripts.init_db
  ```
5. Запустить бота:
  ```bash
  python -m bot.main
  ```
