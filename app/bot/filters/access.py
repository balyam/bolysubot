from aiogram.filters import Filter
from aiogram.types import Message, CallbackQuery
from typing import Union

from app.models import User


class HasAccessFilter(Filter):
    """Фильтр для проверки доступа пользователя"""
    
    async def __call__(self, event: Union[Message, CallbackQuery], user: User) -> bool:
        """
        Проверяет, имеет ли пользователь доступ к боту
        """
        # Заблокированные пользователи не имеют доступа
        if user.is_blocked:
            return False
        
        # Администраторы и одобренные пользователи имеют доступ
        if user.is_admin or user.is_approved:
            return True
        
        return False


class IsAdminFilter(Filter):
    """Фильтр для проверки, является ли пользователь администратором"""
    
    async def __call__(self, event: Union[Message, CallbackQuery], user: User) -> bool:
        return user.is_admin

