from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional

from app.models import Category, User
from app.bot.keyboards.inline import categories_keyboard, main_menu_keyboard, search_results_keyboard
from app.services.search import search_contractors
from app.utils.helpers import h, edit_or_send

router = Router()


@router.callback_query(F.data == "categories")
async def callback_categories(callback: CallbackQuery, session: AsyncSession, state: FSMContext):
    """Показать список категорий верхнего уровня"""
    await state.set_state(None)
    await show_categories(callback, session, parent_id=None)


@router.callback_query(F.data.startswith("category:"))
async def callback_select_category(
    callback: CallbackQuery,
    session: AsyncSession,
    state: FSMContext,
    user: User
):
    """Выбор категории"""
    category_id = int(callback.data.split(":")[1])

    # Проверяем, есть ли подкатегории
    result = await session.execute(
        select(Category.id).where(Category.parent_id == category_id).limit(1)
    )
    has_subcategories = result.scalar_one_or_none() is not None

    if has_subcategories:
        await show_categories(callback, session, parent_id=category_id)
    else:
        await show_contractors_by_category(callback, session, state, user, category_id)


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
        await edit_or_send(
            callback.message,
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
        text = f"📁 Категории в разделе: {h(parent_name)}"
    else:
        text = "📁 Выберите категорию:"

    await edit_or_send(
        callback.message,
        text,
        reply_markup=categories_keyboard(categories, parent_id)
    )
    await callback.answer()


async def show_contractors_by_category(
    callback: CallbackQuery,
    session: AsyncSession,
    state: FSMContext,
    user: User,
    category_id: int
):
    """Показать исполнителей по категории (с учётом региона пользователя)"""
    result = await session.execute(
        select(Category).where(Category.id == category_id)
    )
    category = result.scalar_one_or_none()

    if not category:
        await callback.answer("Категория не найдена", show_alert=True)
        return

    contractors = await search_contractors(
        session=session,
        query="",
        category_id=category_id,
        region_id=user.preferred_region_id
    )

    region_name = user.preferred_region.name if user.preferred_region else "Все регионы"

    if not contractors:
        await edit_or_send(
            callback.message,
            f"❌ В категории '{h(category.name)}' (регион: {h(region_name)}) "
            "пока нет исполнителей.",
            reply_markup=main_menu_keyboard()
        )
        await callback.answer()
        return

    # Формируем список для клавиатуры
    contractor_list = [(c.id, c.name, c.is_premium) for c in contractors]
    title = f"📁 Категория: {h(category.name)}\n📍 Регион: {h(region_name)}"

    # Сохраняем результаты для пагинации и кнопки "Назад" из карточки
    await state.update_data(search_results=contractor_list, query="", results_title=title)

    text = (
        f"{title}\n\n"
        f"Найдено исполнителей: {len(contractors)}\n\n"
        "Выберите исполнителя для просмотра подробной информации:"
    )

    await edit_or_send(
        callback.message,
        text,
        reply_markup=search_results_keyboard(contractor_list, query="")
    )
    await callback.answer()
