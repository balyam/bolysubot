"""
Запуск бота в режиме webhook
"""
import uvicorn
from app_combined import create_app
from config import settings

if __name__ == "__main__":
    if not settings.USE_WEBHOOK:
        print("⚠️  USE_WEBHOOK=False в .env")
        print("Для webhook режима установите USE_WEBHOOK=True")
        print("И укажите WEBHOOK_HOST (например: https://yourdomain.com)")
        exit(1)
    
    if not settings.WEBHOOK_HOST:
        print("❌ WEBHOOK_HOST не указан в .env")
        print("Укажите ваш домен, например: WEBHOOK_HOST=https://yourdomain.com")
        exit(1)
    
    app = create_app()
    
    print("=" * 60)
    print("🚀 ОСИ Алматы (Webhook режим)")
    print("-" * 60)
    print(f"Webhook URL: {settings.webhook_url}")
    print(f"Сервер: http://{settings.WEBAPP_HOST}:{settings.WEBAPP_PORT}")
    print(f"Админка: http://{settings.WEBAPP_HOST}:{settings.WEBAPP_PORT}/admin")
    print("=" * 60)
    
    uvicorn.run(
        app,
        host=settings.WEBAPP_HOST,
        port=settings.WEBAPP_PORT,
        log_level="info" if settings.DEBUG else "warning"
    )


