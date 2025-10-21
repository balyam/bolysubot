from aiogram import Router, F
from aiogram.types import CallbackQuery, InputMediaPhoto
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload

from app.models import Contractor
from app.bot.keyboards.inline import contractor_card_keyboard

router = Router()


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
    
    # Формируем текст карточки
    text = format_contractor_card(contractor)
    
    # Формируем клавиатуру
    keyboard = contractor_card_keyboard(
        contractor_id=contractor.id,
        phone=contractor.phone,
        telegram_username=contractor.telegram_username
    )
    
    # Отправляем карточку с фото или без
    if contractor.photos:
        # Сортируем фото: главное первым
        sorted_photos = sorted(contractor.photos, key=lambda p: (not p.is_main, p.order_index))
        
        if len(sorted_photos) == 1:
            # Одно фото
            await callback.message.answer_photo(
                photo=sorted_photos[0].file_id,
                caption=text,
                reply_markup=keyboard
            )
        else:
            # Несколько фото - отправляем медиагруппу
            media = []
            for i, photo in enumerate(sorted_photos[:10]):  # Максимум 10 фото
                if i == 0:
                    media.append(InputMediaPhoto(media=photo.file_id, caption=text))
                else:
                    media.append(InputMediaPhoto(media=photo.file_id))
            
            await callback.message.answer_media_group(media)
            # Отдельно отправляем клавиатуру
            await callback.message.answer("Выберите действие:", reply_markup=keyboard)
        
        # Удаляем предыдущее сообщение
        try:
            await callback.message.delete()
        except:
            pass
    else:
        # Без фото
        await callback.message.edit_text(text, reply_markup=keyboard)
    
    await callback.answer()


def format_contractor_card(contractor: Contractor) -> str:
    """Форматирование карточки исполнителя"""
    
    # Формируем строку с категориями
    categories_str = ", ".join([cat.name for cat in contractor.categories[:5]])
    if len(contractor.categories) > 5:
        categories_str += f" +{len(contractor.categories) - 5} ещё"
    
    # Рейтинг в звёздах
    rating_stars = "⭐" * int(float(contractor.rating)) if contractor.rating else "Нет оценок"
    
    # Премиум значок
    premium_badge = "⭐ ПРЕМИУМ ⭐\n\n" if contractor.is_premium else ""
    
    # Дополнительные телефоны
    additional_phones_str = ""
    if contractor.additional_phones:
        additional_phones_str = "\n📞 Доп. телефоны: " + ", ".join(contractor.additional_phones)
    
    text = (
        f"{premium_badge}"
        f"📋 {contractor.name}\n\n"
        f"📁 Категории: {categories_str}\n"
        f"📍 Регион: {contractor.region.name}\n"
    )
    
    if contractor.address:
        text += f"🏠 Адрес: {contractor.address}\n"
    
    text += f"\n📞 Телефон: {contractor.phone}{additional_phones_str}\n"
    
    if contractor.telegram_username:
        text += f"✈️ Telegram: @{contractor.telegram_username}\n"
    
    text += f"\n{rating_stars}"
    
    if contractor.reviews_count > 0:
        text += f" ({float(contractor.rating):.1f} / 5.0) - {contractor.reviews_count} отзывов"
    
    if contractor.description:
        text += f"\n\n📝 Описание:\n{contractor.description}"
    
    text += f"\n\n👁 Просмотров: {contractor.views_count + 1}"
    
    return text

