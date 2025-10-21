from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models import User, Region
from app.bot.keyboards.inline import regions_keyboard, main_menu_keyboard

router = Router()


async def show_regions(message: Message, session: AsyncSession, user: User, page: int = 0):
    """Показать список регионов"""
    # Получаем все активные регионы
    result = await session.execute(
        select(Region.id, Region.name)
        .where(Region.is_active == True)
        .order_by(Region.name)
    )
    regions = result.all()
    
    if not regions:
        await message.answer(
            "❌ К сожалению, регионы ещё не добавлены.\n"
            "Пожалуйста, обратитесь к администратору.",
            reply_markup=main_menu_keyboard()
        )
        return
    
    text = "📍 Выберите ваш регион:"
    keyboard = regions_keyboard(regions, page)
    
    if message.from_user:
        await message.answer(text, reply_markup=keyboard)
    else:
        await message.edit_text(text, reply_markup=keyboard)


@router.callback_query(F.data == "change_region")
async def callback_change_region(callback: CallbackQuery, session: AsyncSession, user: User):
    """Изменение региона"""
    result = await session.execute(
        select(Region.id, Region.name)
        .where(Region.is_active == True)
        .order_by(Region.name)
    )
    regions = result.all()
    
    text = "📍 Выберите новый регион:"
    await callback.message.edit_text(text, reply_markup=regions_keyboard(regions))
    await callback.answer()


@router.callback_query(F.data.startswith("region:"))
async def callback_select_region(callback: CallbackQuery, session: AsyncSession, user: User):
    """Выбор региона"""
    region_id = int(callback.data.split(":")[1])
    
    # Обновляем регион пользователя
    user.preferred_region_id = region_id
    await session.commit()
    await session.refresh(user)
    
    region_name = user.preferred_region.name if user.preferred_region else "Не выбран"
    
    text = (
        f"✅ Регион изменён на: {region_name}\n\n"
        "Выберите действие:"
    )
    
    await callback.message.edit_text(text, reply_markup=main_menu_keyboard())
    await callback.answer(f"Регион изменён: {region_name}")


@router.callback_query(F.data.startswith("regions_page:"))
async def callback_regions_page(callback: CallbackQuery, session: AsyncSession, user: User):
    """Пагинация регионов"""
    page = int(callback.data.split(":")[1])
    
    result = await session.execute(
        select(Region.id, Region.name)
        .where(Region.is_active == True)
        .order_by(Region.name)
    )
    regions = result.all()
    
    text = "📍 Выберите ваш регион:"
    await callback.message.edit_text(text, reply_markup=regions_keyboard(regions, page))
    await callback.answer()

