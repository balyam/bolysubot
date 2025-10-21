from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, User as TgUser, Message, CallbackQuery
from typing import Callable, Dict, Any, Awaitable
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session_maker
from app.models import User
from config import settings


class DatabaseMiddleware(BaseMiddleware):
    """Middleware для предоставления сессии БД в хендлеры"""
    
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        async with async_session_maker() as session:
            data["session"] = session
            return await handler(event, data)


class UserMiddleware(BaseMiddleware):
    """Middleware для автоматического сохранения пользователей"""
    
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        session: AsyncSession = data.get("session")
        tg_user: TgUser = data.get("event_from_user")
        
        if session and tg_user:
            # Ищем или создаём пользователя
            from sqlalchemy import select
            from sqlalchemy.orm import selectinload
            
            result = await session.execute(
                select(User)
                .options(selectinload(User.preferred_region))
                .where(User.telegram_id == tg_user.id)
            )
            user = result.scalar_one_or_none()
            
            if not user:
                # Создаём нового пользователя
                # Проверяем, является ли он админом
                is_admin = tg_user.id in settings.admin_ids
                
                # В режиме "open" - автоматически одобряем
                # В режиме "whitelist" - одобряем только админов
                # В режиме "invite_only" - требуется токен (обрабатывается в handler)
                is_approved = (
                    is_admin or 
                    settings.ACCESS_MODE == "open" or
                    (settings.ACCESS_MODE == "whitelist" and is_admin)
                )
                
                user = User(
                    telegram_id=tg_user.id,
                    username=tg_user.username,
                    first_name=tg_user.first_name,
                    last_name=tg_user.last_name,
                    is_admin=is_admin,
                    is_approved=is_approved
                )
                session.add(user)
                await session.commit()
                await session.refresh(user)
            else:
                # Обновляем информацию (если изменилась)
                updated = False
                if user.username != tg_user.username:
                    user.username = tg_user.username
                    updated = True
                if user.first_name != tg_user.first_name:
                    user.first_name = tg_user.first_name
                    updated = True
                if user.last_name != tg_user.last_name:
                    user.last_name = tg_user.last_name
                    updated = True
                
                # Проверяем, не стал ли пользователь админом
                if tg_user.id in settings.admin_ids and not user.is_admin:
                    user.is_admin = True
                    user.is_approved = True  # Админы всегда одобрены
                    updated = True
                
                if updated:
                    await session.commit()
            
            data["user"] = user
        
        return await handler(event, data)


class AccessControlMiddleware(BaseMiddleware):
    """Middleware для проверки доступа к боту"""
    
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        user: User = data.get("user")
        
        # Если пользователь не загружен, пропускаем
        if not user:
            return await handler(event, data)
        
        # Администраторы всегда имеют доступ
        if user.is_admin:
            return await handler(event, data)
        
        # Заблокированные пользователи не имеют доступа
        if user.is_blocked:
            message = "❌ Ваш доступ к боту заблокирован."
            if isinstance(event, Message):
                await event.answer(message)
            elif isinstance(event, CallbackQuery):
                await event.answer(message, show_alert=True)
            return
        
        # Режим "open" - всем доступ
        if settings.ACCESS_MODE == "open":
            return await handler(event, data)
        
        # Проверяем одобрение
        if not user.is_approved:
            # Разрешаем команду /start для ввода токена
            if isinstance(event, Message) and event.text and event.text.startswith("/start"):
                return await handler(event, data)
            
            message = (
                "❌ У вас нет доступа к боту.\n\n"
                "Для получения доступа свяжитесь с администратором "
                "или используйте команду /start с токеном приглашения."
            )
            if isinstance(event, Message):
                await event.answer(message)
            elif isinstance(event, CallbackQuery):
                await event.answer(message, show_alert=True)
            return
        
        return await handler(event, data)

