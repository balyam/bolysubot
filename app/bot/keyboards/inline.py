from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from typing import List, Optional


def main_menu_keyboard() -> InlineKeyboardMarkup:
    """Главное меню бота"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🔍 Поиск", callback_data="search"),
        InlineKeyboardButton(text="📁 Категории", callback_data="categories")
    )
    builder.row(
        InlineKeyboardButton(text="📍 Изменить регион", callback_data="change_region")
    )
    return builder.as_markup()


def regions_keyboard(regions: List[tuple], current_page: int = 0, per_page: int = 8) -> InlineKeyboardMarkup:
    """
    Клавиатура выбора региона с пагинацией
    regions: List[(region_id, region_name)]
    """
    builder = InlineKeyboardBuilder()
    
    # Вычисляем границы страницы
    start_idx = current_page * per_page
    end_idx = start_idx + per_page
    page_regions = regions[start_idx:end_idx]
    
    # Добавляем кнопки регионов (по 2 в ряд)
    for i in range(0, len(page_regions), 2):
        row_buttons = []
        for region_id, region_name in page_regions[i:i+2]:
            row_buttons.append(
                InlineKeyboardButton(text=region_name, callback_data=f"region:{region_id}")
            )
        builder.row(*row_buttons)
    
    # Кнопки пагинации
    total_pages = (len(regions) + per_page - 1) // per_page
    if total_pages > 1:
        nav_buttons = []
        if current_page > 0:
            nav_buttons.append(InlineKeyboardButton(text="⬅️", callback_data=f"regions_page:{current_page-1}"))
        nav_buttons.append(InlineKeyboardButton(text=f"{current_page+1}/{total_pages}", callback_data="noop"))
        if current_page < total_pages - 1:
            nav_buttons.append(InlineKeyboardButton(text="➡️", callback_data=f"regions_page:{current_page+1}"))
        builder.row(*nav_buttons)
    
    return builder.as_markup()


def categories_keyboard(categories: List[tuple], parent_id: Optional[int] = None) -> InlineKeyboardMarkup:
    """
    Клавиатура категорий
    categories: List[(category_id, category_name, icon)]
    """
    builder = InlineKeyboardBuilder()
    
    for category_id, category_name, icon in categories:
        text = f"{icon} {category_name}" if icon else category_name
        builder.row(
            InlineKeyboardButton(text=text, callback_data=f"category:{category_id}")
        )
    
    # Кнопка "Назад"
    if parent_id is not None:
        builder.row(
            InlineKeyboardButton(text="⬅️ Назад", callback_data=f"category_back:{parent_id}")
        )
    
    builder.row(
        InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")
    )
    
    return builder.as_markup()


def contractor_card_keyboard(contractor_id: int, phone: str, telegram_username: Optional[str] = None) -> InlineKeyboardMarkup:
    """Клавиатура карточки исполнителя"""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(text="📞 Позвонить", url=f"tel:{phone}")
    )
    
    if telegram_username:
        builder.row(
            InlineKeyboardButton(text="✈️ Telegram", url=f"https://t.me/{telegram_username}")
        )
    
    builder.row(
        InlineKeyboardButton(text="⭐ Отзывы", callback_data=f"reviews:{contractor_id}"),
        InlineKeyboardButton(text="✍️ Оставить отзыв", callback_data=f"write_review:{contractor_id}")
    )
    
    builder.row(
        InlineKeyboardButton(text="⬅️ Назад к поиску", callback_data="back_to_search")
    )
    
    return builder.as_markup()


def reviews_keyboard(contractor_id: int, page: int = 0, total_pages: int = 1) -> InlineKeyboardMarkup:
    """Клавиатура просмотра отзывов"""
    builder = InlineKeyboardBuilder()
    
    # Навигация по отзывам
    if total_pages > 1:
        nav_buttons = []
        if page > 0:
            nav_buttons.append(InlineKeyboardButton(text="⬅️", callback_data=f"reviews:{contractor_id}:{page-1}"))
        nav_buttons.append(InlineKeyboardButton(text=f"{page+1}/{total_pages}", callback_data="noop"))
        if page < total_pages - 1:
            nav_buttons.append(InlineKeyboardButton(text="➡️", callback_data=f"reviews:{contractor_id}:{page+1}"))
        builder.row(*nav_buttons)
    
    builder.row(
        InlineKeyboardButton(text="✍️ Оставить отзыв", callback_data=f"write_review:{contractor_id}")
    )
    builder.row(
        InlineKeyboardButton(text="⬅️ Назад", callback_data=f"contractor:{contractor_id}")
    )
    
    return builder.as_markup()


def rating_keyboard(contractor_id: int) -> InlineKeyboardMarkup:
    """Клавиатура выбора рейтинга (1-5 звёзд)"""
    builder = InlineKeyboardBuilder()
    
    for rating in range(5, 0, -1):
        stars = "⭐" * rating
        builder.row(
            InlineKeyboardButton(text=f"{stars} ({rating})", callback_data=f"rate:{contractor_id}:{rating}")
        )
    
    builder.row(
        InlineKeyboardButton(text="❌ Отмена", callback_data=f"contractor:{contractor_id}")
    )
    
    return builder.as_markup()


def search_results_keyboard(contractors: List[tuple], query: str, page: int = 0, per_page: int = 5) -> InlineKeyboardMarkup:
    """
    Клавиатура результатов поиска
    contractors: List[(contractor_id, contractor_name, is_premium)]
    """
    builder = InlineKeyboardBuilder()
    
    # Вычисляем границы страницы
    start_idx = page * per_page
    end_idx = start_idx + per_page
    page_contractors = contractors[start_idx:end_idx]
    
    for contractor_id, contractor_name, is_premium in page_contractors:
        prefix = "⭐ " if is_premium else ""
        builder.row(
            InlineKeyboardButton(
                text=f"{prefix}{contractor_name}",
                callback_data=f"contractor:{contractor_id}"
            )
        )
    
    # Пагинация
    total_pages = (len(contractors) + per_page - 1) // per_page
    if total_pages > 1:
        nav_buttons = []
        if page > 0:
            nav_buttons.append(InlineKeyboardButton(text="⬅️", callback_data=f"search_page:{page-1}"))
        nav_buttons.append(InlineKeyboardButton(text=f"{page+1}/{total_pages}", callback_data="noop"))
        if page < total_pages - 1:
            nav_buttons.append(InlineKeyboardButton(text="➡️", callback_data=f"search_page:{page+1}"))
        builder.row(*nav_buttons)
    
    builder.row(
        InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")
    )
    
    return builder.as_markup()


def back_to_main_menu() -> InlineKeyboardMarkup:
    """Простая кнопка возврата в главное меню"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")
    )
    return builder.as_markup()

