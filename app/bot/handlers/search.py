from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User
from app.bot.keyboards.inline import search_results_keyboard, main_menu_keyboard
from app.services.search import search_contractors, log_search
from app.utils.helpers import h, edit_or_send

router = Router()


class SearchStates(StatesGroup):
    """Состояния для поиска"""
    waiting_for_query = State()


@router.callback_query(F.data == "search")
async def callback_search(callback: CallbackQuery, state: FSMContext):
    """Начало поиска"""
    await state.set_state(SearchStates.waiting_for_query)
    await callback.message.answer(
        "🔍 Введите поисковый запрос:\n\n"
        "Например: 'вывоз металлолома', 'ремонт квартир', 'сантехник'"
    )
    await callback.answer()


@router.message(SearchStates.waiting_for_query, F.text)
async def process_search_query(message: Message, state: FSMContext, session: AsyncSession, user: User):
    """Обработка поискового запроса"""
    query = message.text.strip()

    if len(query) < 2:
        await message.answer("❌ Запрос слишком короткий. Введите минимум 2 символа.")
        return

    contractors = await search_contractors(
        session=session,
        query=query,
        region_id=user.preferred_region_id
    )

    # Логируем поиск
    await log_search(
        session=session,
        user_id=user.id,
        query=query,
        region_id=user.preferred_region_id,
        results_count=len(contractors)
    )

    if not contractors:
        await message.answer(
            f"❌ По запросу '{h(query)}' ничего не найдено.\n\n"
            "Попробуйте изменить запрос или выберите категорию.",
            reply_markup=main_menu_keyboard()
        )
        await state.clear()
        return

    # Формируем список для клавиатуры
    contractor_list = [(c.id, c.name, c.is_premium) for c in contractors]

    region_name = user.preferred_region.name if user.preferred_region else "Все регионы"

    text = (
        f"🔍 Результаты поиска: '{h(query)}'\n"
        f"📍 Регион: {h(region_name)}\n\n"
        f"Найдено исполнителей: {len(contractors)}\n\n"
        "Выберите исполнителя для просмотра подробной информации:"
    )

    # Выходим из режима ввода запроса, но сохраняем результаты
    # для пагинации и кнопки "Назад" в карточке исполнителя
    await state.set_state(None)
    await state.update_data(
        search_results=contractor_list,
        query=query,
        results_title=f"🔍 Результаты поиска: '{h(query)}'"
    )

    await message.answer(
        text,
        reply_markup=search_results_keyboard(contractor_list, query=query)
    )


@router.message(SearchStates.waiting_for_query)
async def process_search_non_text(message: Message):
    """Пользователь прислал не текст (фото, стикер и т.п.)"""
    await message.answer("❌ Пожалуйста, отправьте поисковый запрос текстом.")


@router.callback_query(F.data.startswith("search_page:"))
async def callback_search_page(callback: CallbackQuery, state: FSMContext):
    """Пагинация результатов поиска"""
    page = int(callback.data.split(":")[1])

    # Получаем сохранённые результаты
    data = await state.get_data()
    contractor_list = data.get("search_results", [])
    query = data.get("query", "")

    if not contractor_list:
        await callback.answer("Результаты поиска устарели. Начните новый поиск.", show_alert=True)
        return

    await callback.message.edit_reply_markup(
        reply_markup=search_results_keyboard(contractor_list, query=query, page=page)
    )
    await callback.answer()


@router.callback_query(F.data == "back_to_search")
async def callback_back_to_search(callback: CallbackQuery, state: FSMContext):
    """Возврат к результатам поиска"""
    data = await state.get_data()
    contractor_list = data.get("search_results", [])
    query = data.get("query", "")

    if not contractor_list:
        await edit_or_send(
            callback.message,
            "Результаты поиска устарели.\n"
            "Вернитесь в главное меню и начните новый поиск.",
            reply_markup=main_menu_keyboard()
        )
        await callback.answer()
        return

    title = data.get("results_title") or f"🔍 Результаты поиска: '{h(query)}'"
    text = (
        f"{title}\n\n"
        f"Найдено исполнителей: {len(contractor_list)}\n\n"
        "Выберите исполнителя для просмотра подробной информации:"
    )

    await edit_or_send(
        callback.message,
        text,
        reply_markup=search_results_keyboard(contractor_list, query=query)
    )
    await callback.answer()
