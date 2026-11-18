from datetime import datetime
from html import escape
from typing import Optional

from aiogram.exceptions import TelegramBadRequest
from aiogram.types import Message, InlineKeyboardMarkup


def h(value: Optional[object]) -> str:
    """Экранировать пользовательские данные для ParseMode.HTML"""
    if value is None:
        return ""
    return escape(str(value), quote=False)


async def edit_or_send(
    message: Message,
    text: str,
    reply_markup: Optional[InlineKeyboardMarkup] = None
) -> None:
    """
    Отредактировать текстовое сообщение. Если сообщение медийное (например,
    карточка исполнителя с фото) — его текст редактировать нельзя, поэтому
    отправляем новое сообщение и удаляем старое.
    """
    if message.text is not None:
        await message.edit_text(text, reply_markup=reply_markup)
        return

    await message.answer(text, reply_markup=reply_markup)
    try:
        await message.delete()
    except TelegramBadRequest:
        pass


def format_phone(phone: str) -> str:
    """Форматировать номер телефона"""
    # Убираем все символы кроме цифр и +
    cleaned = "".join(c for c in phone if c.isdigit() or c == "+")
    return cleaned


def format_datetime(dt: datetime) -> str:
    """Форматировать дату и время"""
    return dt.strftime("%d.%m.%Y %H:%M")


def format_date(dt: datetime) -> str:
    """Форматировать дату"""
    return dt.strftime("%d.%m.%Y")


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """Обрезать текст до указанной длины"""
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix
