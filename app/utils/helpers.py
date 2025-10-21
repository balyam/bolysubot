from datetime import datetime
from typing import Optional


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

