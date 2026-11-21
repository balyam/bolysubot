from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.models import Contractor, Review, User
from app.bot.keyboards.inline import reviews_keyboard, rating_keyboard, back_to_main_menu
from app.utils.helpers import h, edit_or_send

router = Router()

REVIEWS_PER_PAGE = 3
COMMENT_MAX_LENGTH = 500


class ReviewStates(StatesGroup):
    """Состояния для написания отзыва"""
    waiting_for_rating = State()
    waiting_for_comment = State()


async def finish_review_flow(state: FSMContext) -> None:
    """Выйти из сценария отзыва, сохранив остальные данные (результаты поиска)"""
    data = await state.get_data()
    await state.set_data({k: v for k, v in data.items() if k not in ("contractor_id", "rating")})
    await state.set_state(None)


async def _has_review(session: AsyncSession, contractor_id: int, user_id: int) -> bool:
    result = await session.execute(
        select(Review.id)
        .where(Review.contractor_id == contractor_id, Review.user_id == user_id)
        .limit(1)
    )
    return result.scalar_one_or_none() is not None


@router.callback_query(F.data.startswith("reviews:"))
async def callback_show_reviews(callback: CallbackQuery, session: AsyncSession):
    """Показать отзывы исполнителя"""
    parts = callback.data.split(":")
    contractor_id = int(parts[1])
    page = int(parts[2]) if len(parts) > 2 else 0

    # Получаем исполнителя
    result = await session.execute(
        select(Contractor).where(Contractor.id == contractor_id)
    )
    contractor = result.scalar_one_or_none()

    if not contractor:
        await callback.answer("Исполнитель не найден", show_alert=True)
        return

    # Получаем отзывы
    result = await session.execute(
        select(Review)
        .where(
            Review.contractor_id == contractor_id,
            Review.is_visible == True,
            Review.is_moderated == True
        )
        .order_by(Review.created_at.desc())
    )
    reviews = result.scalars().all()

    if not reviews:
        text = (
            f"📋 {h(contractor.name)}\n\n"
            "У этого исполнителя пока нет отзывов.\n"
            "Будьте первым, кто оставит отзыв!"
        )
        await edit_or_send(callback.message, text, reply_markup=reviews_keyboard(contractor_id))
        await callback.answer()
        return

    # Пагинация
    total_pages = (len(reviews) + REVIEWS_PER_PAGE - 1) // REVIEWS_PER_PAGE
    page = max(0, min(page, total_pages - 1))
    start_idx = page * REVIEWS_PER_PAGE
    page_reviews = reviews[start_idx:start_idx + REVIEWS_PER_PAGE]

    # Формируем текст
    text = f"📋 {h(contractor.name)}\n\n"
    text += f"⭐ Рейтинг: {float(contractor.rating):.1f} / 5.0 ({contractor.reviews_count} отзывов)\n\n"
    text += "📝 Отзывы:\n\n"

    for i, review in enumerate(page_reviews, start=start_idx + 1):
        stars = "⭐" * review.rating
        user_name = h(review.user_name or "Аноним")
        date = review.created_at.strftime("%d.%m.%Y")

        text += f"{i}. {stars} {user_name} ({date})\n"
        if review.comment:
            text += f"   {h(review.comment)}\n"
        text += "\n"

    keyboard = reviews_keyboard(contractor_id, page, total_pages)
    await edit_or_send(callback.message, text, reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data.startswith("write_review:"))
async def callback_write_review(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
    user: User
):
    """Начать написание отзыва"""
    contractor_id = int(callback.data.split(":")[1])

    # Проверяем сразу, а не после того, как пользователь напишет комментарий
    if await _has_review(session, contractor_id, user.id):
        await callback.answer(
            "Вы уже оставляли отзыв этому исполнителю.",
            show_alert=True
        )
        return

    await state.set_state(ReviewStates.waiting_for_rating)
    await state.update_data(contractor_id=contractor_id)

    await edit_or_send(
        callback.message,
        "⭐ Оцените исполнителя от 1 до 5 звёзд:",
        reply_markup=rating_keyboard(contractor_id)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("rate:"))
async def callback_rate_contractor(callback: CallbackQuery, state: FSMContext):
    """Выбор рейтинга"""
    parts = callback.data.split(":")
    contractor_id = int(parts[1])
    rating = int(parts[2])

    if not 1 <= rating <= 5:
        await callback.answer("Некорректная оценка", show_alert=True)
        return

    # Проверяем состояние и что оценка относится к тому же исполнителю
    current_state = await state.get_state()
    data = await state.get_data()
    if current_state != ReviewStates.waiting_for_rating or data.get("contractor_id") != contractor_id:
        await callback.answer("Ошибка: начните написание отзыва заново", show_alert=True)
        return

    # Сохраняем рейтинг
    await state.update_data(rating=rating)
    await state.set_state(ReviewStates.waiting_for_comment)

    stars = "⭐" * rating
    text = (
        f"Ваша оценка: {stars}\n\n"
        f"📝 Напишите комментарий к отзыву (максимум {COMMENT_MAX_LENGTH} символов) "
        "или нажмите /skip чтобы пропустить:"
    )

    await edit_or_send(callback.message, text, reply_markup=back_to_main_menu())
    await callback.answer()


@router.message(ReviewStates.waiting_for_comment, F.text)
async def process_review_comment(message: Message, state: FSMContext, session: AsyncSession, user: User):
    """Обработка комментария к отзыву"""
    comment = None if message.text == "/skip" else message.text.strip()

    # Валидация длины комментария
    if comment and len(comment) > COMMENT_MAX_LENGTH:
        await message.answer(
            f"❌ Комментарий слишком длинный ({len(comment)} символов).\n"
            f"Максимальная длина комментария: {COMMENT_MAX_LENGTH} символов.\n\n"
            "Пожалуйста, сократите комментарий и отправьте снова:"
        )
        return

    # Получаем данные из состояния
    data = await state.get_data()
    contractor_id = data.get("contractor_id")
    rating = data.get("rating")

    if not contractor_id or not rating:
        await message.answer("Ошибка: данные отзыва не найдены. Начните заново.")
        await finish_review_flow(state)
        return

    # Повторная проверка (на случай двух параллельных сценариев)
    if await _has_review(session, contractor_id, user.id):
        await message.answer(
            "❌ Вы уже оставляли отзыв этому исполнителю.\n"
            "Редактирование отзывов пока не поддерживается.",
            reply_markup=back_to_main_menu()
        )
        await finish_review_flow(state)
        return

    # Создаём отзыв. Рейтинг исполнителя пересчитывается после модерации
    # (в админке), поэтому здесь его не трогаем.
    user_name = user.first_name or user.username or "Аноним"
    review = Review(
        contractor_id=contractor_id,
        user_id=user.id,
        user_name=user_name,
        rating=rating,
        comment=comment,
        is_moderated=False,  # Требует модерации
        is_visible=True
    )
    session.add(review)
    try:
        await session.commit()
    except IntegrityError:
        # Параллельный отзыв (двойное нажатие) упёрся в uq_reviews_user_contractor
        await session.rollback()
        await message.answer(
            "❌ Вы уже оставляли отзыв этому исполнителю.",
            reply_markup=back_to_main_menu()
        )
        await finish_review_flow(state)
        return

    await message.answer(
        "✅ Спасибо! Ваш отзыв отправлен на модерацию.\n"
        "После проверки он появится в профиле исполнителя.",
        reply_markup=back_to_main_menu()
    )

    await finish_review_flow(state)


@router.message(ReviewStates.waiting_for_comment)
async def process_review_non_text(message: Message):
    """Пользователь прислал не текст"""
    await message.answer("❌ Отправьте комментарий текстом или нажмите /skip.")
