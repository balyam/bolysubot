from fastapi import FastAPI
from sqladmin import Admin
from starlette.middleware.sessions import SessionMiddleware
from sqlalchemy import create_engine

from config import settings
from app.admin.auth import AdminAuth
from app.admin.views import (
    UserAdmin,
    RegionAdmin,
    CategoryAdmin,
    ContractorAdmin,
    ContractorPhotoAdmin,
    ReviewAdmin
)


def create_admin_app() -> FastAPI:
    """Создать FastAPI приложение с админ-панелью"""
    
    app = FastAPI(
        title="BolySuBot Admin",
        description="Админ-панель для управления ботом поиска исполнителей",
        version="1.0.0"
    )
    
    # Добавляем middleware для сессий (требуется для аутентификации)
    app.add_middleware(
        SessionMiddleware,
        secret_key=settings.ADMIN_SECRET_KEY
    )
    
    # Создаём синхронный engine для SQLAdmin (он не поддерживает async engine)
    sync_database_url = settings.DATABASE_URL.replace("+asyncpg", "")
    sync_engine = create_engine(
        sync_database_url.replace("postgresql+asyncpg", "postgresql"),
        echo=settings.DEBUG,
        pool_pre_ping=True
    )
    
    # Создаём админ-панель
    authentication_backend = AdminAuth(secret_key=settings.ADMIN_SECRET_KEY)
    admin = Admin(
        app=app,
        engine=sync_engine,
        title="BolySuBot Admin",
        authentication_backend=authentication_backend
    )
    
    # Регистрируем модели
    admin.add_view(RegionAdmin)
    admin.add_view(CategoryAdmin)
    admin.add_view(ContractorAdmin)
    admin.add_view(ContractorPhotoAdmin)
    admin.add_view(ReviewAdmin)
    admin.add_view(UserAdmin)
    
    @app.get("/")
    async def root():
        return {"message": "BolySuBot Admin API. Go to /admin to access admin panel."}
    
    return app

