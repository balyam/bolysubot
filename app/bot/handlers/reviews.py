from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from app.models import Contractor, Review, User
from app.bot.keyboards.inline import reviews_keyboard, rating_keyboard, back_to_main_menu

router = Router()

REVIEWS_PER_PAGE = 3


class ReviewStates(StatesGroup):
    """Состояния для написания отзыва"""
    waiting_for_rating = State()
    waiting_for_comment = State()


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
            f"📋 {contractor.name}\n\n"
            "У этого исполнителя пока нет отзывов.\n"
            "Будьте первым, кто оставит отзыв!"
        )
        keyboard = rating_keyboard(contractor_id)
        await callback.message.edit_text(text, reply_markup=keyboard)
        await callback.answer()
        return
    
    # Пагинация
    total_pages = (len(reviews) + REVIEWS_PER_PAGE - 1) // REVIEWS_PER_PAGE
    start_idx = page * REVIEWS_PER_PAGE
    end_idx = start_idx + REVIEWS_PER_PAGE
    page_reviews = reviews[start_idx:end_idx]
    
    # Формируем текст
    text = f"📋 {contractor.name}\n\n"
    text += f"⭐ Рейтинг: {float(contractor.rating):.1f} / 5.0 ({contractor.reviews_count} отзывов)\n\n"
    text += "📝 Отзывы:\n\n"
    
    for i, review in enumerate(page_reviews, start=start_idx + 1):
        stars = "⭐" * review.rating
        user_name = review.user_name or "Аноним"
        date = review.created_at.strftime("%d.%m.%Y")
        
        text += f"{i}. {stars} {user_name} ({date})\n"
        if review.comment:
            text += f"   {review.comment}\n"
        text += "\n"
    
    keyboard = reviews_keyboard(contractor_id, page, total_pages)
    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data.startswith("write_review:"))
async def callback_write_review(callback: CallbackQuery, state: FSMContext):
    """Начать написание отзыва"""
    contractor_id = int(callback.data.split(":")[1])
    
    await state.set_state(ReviewStates.waiting_for_rating)
    await state.update_data(contractor_id=contractor_id)
    
    await callback.message.edit_text(
        "⭐ Оцените исполнителя от 1 до 5 звёзд:",
        reply_markup=rating_keyboard(contractor_id)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("rate:"))
async def callback_rate_contractor(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Выбор рейтинга"""
    parts = callback.data.split(":")
    contractor_id = int(parts[1])
    rating = int(parts[2])
    
    # Проверяем состояние
    current_state = await state.get_state()
    if current_state != ReviewStates.waiting_for_rating:
        await callback.answer("Ошибка: неверное состояние", show_alert=True)
        return
    
    # Сохраняем рейтинг
    await state.update_data(rating=rating)
    await state.set_state(ReviewStates.waiting_for_comment)
    
    # Получаем исполнителя
    result = await session.execute(
        select(Contractor.name).where(Contractor.id == contractor_id)
    )
    contractor_name = result.scalar_one_or_none()
    
    stars = "⭐" * rating
    text = (
        f"Ваша оценка: {stars}\n\n"
        "📝 Напишите комментарий к отзыву или нажмите /skip чтобы пропустить:"
    )
    
    await callback.message.edit_text(text, reply_markup=back_to_main_menu())
    await callback.answer()


@router.message(ReviewStates.waiting_for_comment, F.text)
async def process_review_comment(message: Message, state: FSMContext, session: AsyncSession, user: User):
    """Обработка комментария к отзыву"""
    comment = None if message.text == "/skip" else message.text.strip()
    
    # Получаем данные из состояния
    data = await state.get_data()
    contractor_id = data.get("contractor_id")
    rating = data.get("rating")
    
    if not contractor_id or not rating:
        await message.answer("Ошибка: данные отзыва не найдены. Начните заново.")
        await state.clear()
        return
    
    # Проверяем, не оставлял ли пользователь уже отзыв
    result = await session.execute(
        select(Review)
        .where(
            Review.contractor_id == contractor_id,
            Review.user_id == user.id
        )
    )
    existing_review = result.scalar_one_or_none()
    
    if existing_review:
        await message.answer(
            "❌ Вы уже оставляли отзыв этому исполнителю.\n"
            "Редактирование отзывов пока не поддерживается.",
            reply_markup=back_to_main_menu()
        )
        await state.clear()
        return
    
    # Создаём отзыв
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
    
    # Обновляем рейтинг исполнителя
    await update_contractor_rating(session, contractor_id)
    
    await session.commit()
    
    await message.answer(
        "✅ Спасибо! Ваш отзыв отправлен на модерацию.\n"
        "После проверки он появится в профиле исполнителя.",
        reply_markup=back_to_main_menu()
    )
    
    await state.clear()


async def update_contractor_rating(session: AsyncSession, contractor_id: int):
    """Пересчитать средний рейтинг исполнителя"""
    from sqlalchemy import update
    
    # Вычисляем средний рейтинг
    result = await session.execute(
        select(
            func.avg(Review.rating).label("avg_rating"),
            func.count(Review.id).label("count")
        )
        .where(
            Review.contractor_id == contractor_id,
            Review.is_visible == True
        )
    )
    stats = result.one()
    
    avg_rating = float(stats.avg_rating) if stats.avg_rating else 0
    count = stats.count
    
    # Обновляем исполнителя
    await session.execute(
        update(Contractor)
        .where(Contractor.id == contractor_id)
        .values(rating=avg_rating, reviews_count=count)
    )

