from aiogram import Router, F
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional

from app.models import Category
from app.bot.keyboards.inline import categories_keyboard, main_menu_keyboard

router = Router()


@router.callback_query(F.data == "categories")
async def callback_categories(callback: CallbackQuery, session: AsyncSession):
    """Показать список категорий верхнего уровня"""
    await show_categories(callback, session, parent_id=None)


@router.callback_query(F.data.startswith("category:"))
async def callback_select_category(callback: CallbackQuery, session: AsyncSession):
    """Выбор категории"""
    category_id = int(callback.data.split(":")[1])
    
    # Проверяем, есть ли подкатегории
    result = await session.execute(
        select(Category)
        .where(Category.parent_id == category_id)
        .order_by(Category.order_index, Category.name)
    )
    subcategories = result.scalars().all()
    
    if subcategories:
        # Показываем подкатегории
        await show_categories(callback, session, parent_id=category_id)
    else:
        # Показываем исполнителей в этой категории
        await show_contractors_by_category(callback, session, category_id)


@router.callback_query(F.data.startswith("category_back:"))
async def callback_category_back(callback: CallbackQuery, session: AsyncSession):
    """Возврат к родительской категории"""
    parent_id_str = callback.data.split(":")[1]
    parent_id = int(parent_id_str) if parent_id_str != "None" else None
    
    if parent_id is None:
        await show_categories(callback, session, parent_id=None)
    else:
        # Находим родителя родителя
        result = await session.execute(
            select(Category.parent_id).where(Category.id == parent_id)
        )
        grandparent_id = result.scalar_one_or_none()
        await show_categories(callback, session, parent_id=grandparent_id)


async def show_categories(callback: CallbackQuery, session: AsyncSession, parent_id: Optional[int] = None):
    """Показать категории"""
    result = await session.execute(
        select(Category.id, Category.name, Category.icon)
        .where(Category.parent_id == parent_id)
        .order_by(Category.order_index, Category.name)
    )
    categories = result.all()
    
    if not categories:
        await callback.message.edit_text(
            "❌ Категории не найдены.",
            reply_markup=main_menu_keyboard()
        )
        await callback.answer()
        return
    
    # Получаем название родительской категории
    if parent_id:
        result = await session.execute(
            select(Category.name).where(Category.id == parent_id)
        )
        parent_name = result.scalar_one_or_none()
        text = f"📁 Категории в разделе: {parent_name}"
    else:
        text = "📁 Выберите категорию:"
    
    await callback.message.edit_text(
        text,
        reply_markup=categories_keyboard(categories, parent_id)
    )
    await callback.answer()


async def show_contractors_by_category(callback: CallbackQuery, session: AsyncSession, category_id: int):
    """Показать исполнителей по категории"""
    from sqlalchemy.orm import selectinload
    from app.models import Contractor, User
    from app.bot.keyboards.inline import search_results_keyboard
    
    # Получаем пользователя
    user: User = callback.message.chat
    
    # Получаем категорию
    result = await session.execute(
        select(Category).where(Category.id == category_id)
    )
    category = result.scalar_one_or_none()
    
    if not category:
        await callback.answer("Категория не найдена", show_alert=True)
        return
    
    # Получаем исполнителей в этой категории
    from app.services.search import search_contractors
    contractors = await search_contractors(
        session=session,
        query="",
        category_id=category_id,
        region_id=None  # Можно добавить фильтр по региону
    )
    
    if not contractors:
        await callback.message.edit_text(
            f"❌ В категории '{category.name}' пока нет исполнителей.",
            reply_markup=main_menu_keyboard()
        )
        await callback.answer()
        return
    
    # Формируем список для клавиатуры
    contractor_list = [(c.id, c.name, c.is_premium) for c in contractors]
    
    text = f"📁 Категория: {category.name}\n\n" \
           f"Найдено исполнителей: {len(contractors)}\n\n" \
           "Выберите исполнителя для просмотра подробной информации:"
    
    await callback.message.edit_text(
        text,
        reply_markup=search_results_keyboard(contractor_list, query="")
    )
    await callback.answer()

