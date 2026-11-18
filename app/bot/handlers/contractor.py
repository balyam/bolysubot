from aiogram import Router, F
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery, InputMediaPhoto
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload

from app.models import Contractor
from app.bot.keyboards.inline import contractor_card_keyboard
from app.utils.helpers import h, edit_or_send, truncate_text

router = Router()

# Лимиты Telegram
CAPTION_LIMIT = 1024
# Запас под остальные поля карточки (лимит сообщения — 4096)
DESCRIPTION_LIMIT = 3000


@router.callback_query(F.data.startswith("contractor:"))
async def callback_show_contractor(callback: CallbackQuery, session: AsyncSession):
    """Показать карточку исполнителя"""
    contractor_id = int(callback.data.split(":")[1])

    # Получаем исполнителя с фотографиями
    result = await session.execute(
        select(Contractor)
        .options(
            selectinload(Contractor.photos),
            selectinload(Contractor.region),
            selectinload(Contractor.categories)
        )
        .where(Contractor.id == contractor_id)
    )
    contractor = result.scalar_one_or_none()

    if not contractor or not contractor.is_active:
        await callback.answer("Исполнитель не найден или неактивен", show_alert=True)
        return

    # Увеличиваем счётчик просмотров
    await session.execute(
        update(Contractor)
        .where(Contractor.id == contractor_id)
        .values(views_count=Contractor.views_count + 1)
    )
    await session.commit()

    text = format_contractor_card(contractor)
    keyboard = contractor_card_keyboard(
        contractor_id=contractor.id,
        phone=contractor.phone,
        telegram_username=contractor.telegram_username
    )

    if not contractor.photos:
        await edit_or_send(callback.message, text, reply_markup=keyboard)
        await callback.answer()
        return

    # Сортируем фото: главное первым
    sorted_photos = sorted(contractor.photos, key=lambda p: (not p.is_main, p.order_index))[:10]
    caption_fits = len(text) <= CAPTION_LIMIT

    if len(sorted_photos) == 1:
        if caption_fits:
            await callback.message.answer_photo(
                photo=sorted_photos[0].file_id,
                caption=text,
                reply_markup=keyboard
            )
        else:
            # Описание не влезает в подпись — фото отдельно, текст с кнопками отдельно
            await callback.message.answer_photo(photo=sorted_photos[0].file_id)
            await callback.message.answer(text, reply_markup=keyboard)
    else:
        # Медиагруппа не поддерживает клавиатуру — кнопки отдельным сообщением
        media = [
            InputMediaPhoto(
                media=photo.file_id,
                caption=text if (i == 0 and caption_fits) else None
            )
            for i, photo in enumerate(sorted_photos)
        ]
        await callback.message.answer_media_group(media)
        await callback.message.answer(
            "Выберите действие:" if caption_fits else text,
            reply_markup=keyboard
        )

    # Удаляем предыдущее сообщение
    try:
        await callback.message.delete()
    except TelegramBadRequest:
        pass

    await callback.answer()


def format_contractor_card(contractor: Contractor) -> str:
    """Форматирование карточки исполнителя (HTML)"""

    # Формируем строку с категориями
    categories_str = ", ".join(h(cat.name) for cat in contractor.categories[:5])
    if len(contractor.categories) > 5:
        categories_str += f" +{len(contractor.categories) - 5} ещё"

    # Рейтинг в звёздах
    rating_stars = "⭐" * int(float(contractor.rating)) if contractor.rating else "Нет оценок"

    # Премиум значок
    premium_badge = "⭐ ПРЕМИУМ ⭐\n\n" if contractor.is_premium else ""

    # Дополнительные телефоны
    additional_phones_str = ""
    if contractor.additional_phones:
        additional_phones_str = "\n📞 Доп. телефоны: " + ", ".join(
            h(p) for p in contractor.additional_phones
        )

    text = (
        f"{premium_badge}"
        f"📋 {h(contractor.name)}\n\n"
        f"📁 Категории: {categories_str}\n"
        f"📍 Регион: {h(contractor.region.name)}\n"
    )

    if contractor.address:
        text += f"🏠 Адрес: {h(contractor.address)}\n"

    text += f"\n📞 Телефон: {h(contractor.phone)}{additional_phones_str}\n"

    if contractor.telegram_username:
        text += f"✈️ Telegram: @{h(contractor.telegram_username)}\n"

    text += f"\n{rating_stars}"

    if contractor.reviews_count > 0:
        text += f" ({float(contractor.rating):.1f} / 5.0) - {contractor.reviews_count} отзывов"

    if contractor.description:
        text += f"\n\n📝 Описание:\n{_escaped_description(contractor.description)}"

    text += f"\n\n👁 Просмотров: {contractor.views_count + 1}"

    return text


def _escaped_description(description: str) -> str:
    """
    Экранированное описание длиной не более DESCRIPTION_LIMIT.
    Обрезаем исходный текст (а не экранированный), чтобы не разрезать
    HTML-сущность вроде &lt;, но длину считаем уже после экранирования.
    """
    max_raw = DESCRIPTION_LIMIT
    escaped = h(truncate_text(description, max_raw))
    while len(escaped) > DESCRIPTION_LIMIT:
        max_raw = max(1, max_raw * DESCRIPTION_LIMIT // len(escaped) - 10)
        escaped = h(truncate_text(description, max_raw))
    return escaped
