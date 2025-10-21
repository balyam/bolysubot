import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from config import settings
from app.bot.handlers import main_router
from app.bot.middlewares import DatabaseMiddleware, UserMiddleware, AccessControlMiddleware

# Настройка логирования
logging.basicConfig(
    level=logging.INFO if settings.DEBUG else logging.WARNING,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


async def main():
    """Запуск бота"""
    
    # Инициализация бота и диспетчера
    bot = Bot(
        token=settings.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    
    dp = Dispatcher()
    
    # Регистрация middlewares
    dp.update.middleware(DatabaseMiddleware())
    dp.update.middleware(UserMiddleware())
    dp.update.middleware(AccessControlMiddleware())
    
    # Регистрация роутеров
    dp.include_router(main_router)
    
    logger.info("Бот запущен")
    
    try:
        # Удаляем webhook (если был установлен)
        await bot.delete_webhook(drop_pending_updates=True)
        
        # Запускаем polling
        await dp.start_polling(bot)
    finally:
        await bot.session.close()
        logger.info("Бот остановлен")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Остановка бота по Ctrl+C")
