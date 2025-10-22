"""
Объединенное приложение: бот + админка в одном FastAPI
Работает с webhook
"""
import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import Update
from aiogram.webhook.aiohttp_server import SimpleRequestHandler

from config import settings
from app.bot.handlers import main_router
from app.bot.middlewares import DatabaseMiddleware, UserMiddleware, AccessControlMiddleware
from app.admin.app import create_admin_app

# Настройка логирования
logging.basicConfig(
    level=logging.INFO if settings.DEBUG else logging.WARNING,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

# Глобальные переменные для бота
bot: Bot = None
dp: Dispatcher = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Управление жизненным циклом приложения"""
    global bot, dp
    
    # Startup
    logger.info("Starting application...")
    
    # Инициализация бота
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
    
    polling_task = None
    
    if settings.USE_WEBHOOK:
        # Настройка webhook
        webhook_url = settings.webhook_url
        if not webhook_url:
            raise ValueError("WEBHOOK_HOST must be set when USE_WEBHOOK=True")
        
        logger.info(f"Setting webhook: {webhook_url}")
        await bot.set_webhook(
            url=webhook_url,
            drop_pending_updates=True,
            secret_token=settings.WEBHOOK_SECRET or None
        )
        logger.info("Webhook set successfully")
    else:
        # Удаляем webhook для polling режима
        await bot.delete_webhook(drop_pending_updates=True)
        logger.info("Webhook deleted, starting polling mode...")
        
        # Запускаем polling в фоновой задаче
        async def run_polling():
            try:
                await dp.start_polling(bot)
            except Exception as e:
                logger.error(f"Polling error: {e}")
        
        polling_task = asyncio.create_task(run_polling())
        logger.info("Polling task started")
    
    logger.info("Bot started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down...")
    
    # Останавливаем polling если запущен
    if polling_task and not polling_task.done():
        polling_task.cancel()
        try:
            await polling_task
        except asyncio.CancelledError:
            pass
    
    await bot.session.close()
    logger.info("Application stopped")


def create_app() -> FastAPI:
    """Создать объединенное FastAPI приложение с ботом и админкой"""
    
    # Создаем базовое приложение с админкой
    app = create_admin_app()
    
    # Обновляем lifespan для включения бота
    app.router.lifespan_context = lifespan
    
    # Добавляем endpoint для webhook
    if settings.USE_WEBHOOK:
        @app.post(settings.WEBHOOK_PATH)
        async def webhook_handler(request: Request) -> dict:
            """Обработчик webhook от Telegram"""
            # Проверка секретного токена
            if settings.WEBHOOK_SECRET:
                token = request.headers.get("X-Telegram-Bot-Api-Secret-Token")
                if token != settings.WEBHOOK_SECRET:
                    logger.warning("Invalid webhook secret token")
                    return {"status": "error", "message": "Invalid secret token"}
            
            # Получаем update
            try:
                update_data = await request.json()
                update = Update(**update_data)
                await dp.feed_update(bot, update)
                return {"status": "ok"}
            except Exception as e:
                logger.error(f"Error processing webhook: {e}")
                return {"status": "error", "message": str(e)}
    
    @app.get("/")
    async def root():
        """Корневой эндпоинт"""
        return {
            "message": "ОСИ Алматы API",
            "admin": "/admin",
            "webhook_mode": settings.USE_WEBHOOK,
            "webhook_path": settings.WEBHOOK_PATH if settings.USE_WEBHOOK else None
        }
    
    @app.get("/health")
    async def health_check():
        """Проверка здоровья приложения"""
        return {
            "status": "healthy",
            "bot_mode": "webhook" if settings.USE_WEBHOOK else "polling"
        }
    
    return app


if __name__ == "__main__":
    import uvicorn
    
    app = create_app()
    
    print("=" * 60)
    print("🚀 ОСИ Алматы запущен!")
    print("-" * 60)
    print(f"Режим бота: {'Webhook' if settings.USE_WEBHOOK else 'Polling'}")
    if settings.USE_WEBHOOK:
        print(f"Webhook URL: {settings.webhook_url}")
    print(f"Админка: http://{settings.WEBAPP_HOST}:{settings.WEBAPP_PORT}/admin")
    print(f"Логин: {settings.ADMIN_USERNAME}")
    print(f"Пароль: {settings.ADMIN_PASSWORD}")
    print("=" * 60)
    
    uvicorn.run(
        app,
        host=settings.WEBAPP_HOST,
        port=settings.WEBAPP_PORT,
        log_level="info" if settings.DEBUG else "warning"
    )


