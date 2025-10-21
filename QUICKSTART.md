# 🚀 Быстрый старт

Это краткое руководство по запуску бота за 5 минут.

## 1. Установка зависимостей

```bash
# Создайте виртуальное окружение
python -m venv venv

# Активируйте его (Windows)
venv\Scripts\activate

# Установите пакеты
pip install -r requirements.txt
```

## 2. Настройка PostgreSQL

```sql
-- Создайте БД в PostgreSQL
CREATE DATABASE osialmatybot;
```

## 3. Создайте .env файл

```env
BOT_TOKEN=your_bot_token_here
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/osialmatybot
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin123
ADMIN_SECRET_KEY=super-secret-key-change-me
DEBUG=True
```

## 4. Примените миграции

```bash
# Создайте миграцию
alembic revision --autogenerate -m "Initial"

# Примените
alembic upgrade head
```

## 5. Запустите админку

```bash
python admin_run.py
```

Откройте: http://localhost:8000/admin
- Логин: admin
- Пароль: admin123

## 6. Добавьте данные в админке

### Регионы:
- Создайте несколько регионов (Москва, СПб и т.д.)

### Категории:
- 🚚 Вывоз мусора
- 🔧 Ремонт квартир
- 💼 Юридические услуги
- 🏗 Строительство

### Исполнители:
- Добавьте 2-3 исполнителя для теста
- Укажите телефон, регион, категории

## 7. Запустите бота

В новом терминале:

```bash
python main.py
```

## 8. Тестируйте!

Найдите вашего бота в Telegram и попробуйте:
- `/start` - начало работы
- Выберите регион
- Попробуйте поиск
- Посмотрите категории
- Оставьте отзыв

---

## Возможные проблемы

### Ошибка подключения к БД
Проверьте `DATABASE_URL` в `.env` - правильные ли логин/пароль/хост/порт.

### Бот не отвечает
Проверьте `BOT_TOKEN` - получили ли вы его от @BotFather.

### Ошибка импорта модулей
Убедитесь, что виртуальное окружение активировано и все пакеты установлены.

---

**Готово!** Теперь у вас работающий бот. Детали смотрите в [README.md](README.md).

