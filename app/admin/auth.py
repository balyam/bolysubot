from typing import Optional
from starlette.requests import Request
from starlette.responses import RedirectResponse
from sqladmin.authentication import AuthenticationBackend

from config import settings


class AdminAuth(AuthenticationBackend):
    """Простая аутентификация для админ-панели"""
    
    async def login(self, request: Request) -> bool:
        form = await request.form()
        username = form.get("username")
        password = form.get("password")
        
        # Простая проверка логина/пароля
        if username == settings.ADMIN_USERNAME and password == settings.ADMIN_PASSWORD:
            # Сохраняем в сессии
            request.session.update({"token": "authenticated"})
            return True
        
        return False
    
    async def logout(self, request: Request) -> bool:
        request.session.clear()
        return True
    
    async def authenticate(self, request: Request) -> bool:
        # Возвращаем True если аутентифицирован, False если нет
        token = request.session.get("token")
        if not token or token != "authenticated":
            return False
        return True

