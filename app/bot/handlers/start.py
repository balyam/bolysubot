from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User
from app.bot.keyboards.inline import main_menu_keyboard
from app.utils.helpers import h, edit_or_send
from config import settings

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message, session: AsyncSession, user: User, state: FSMContext):
    """Обработка команды /start"""
    await state.clear()
    
    # Проверка доступа
    if not user.is_approved and not user.is_admin:
        # Проверяем, есть ли токен в команде
        args = message.text.split(maxsplit=1)
        if len(args) > 1:
            token = args[1].strip()
            
            # Проверяем токен приглашения
            if settings.ACCESS_MODE == "invite_only" and token == settings.INVITE_TOKEN:
                user.is_approved = True
                user.invite_token = token
                await session.commit()
                
                await message.answer(
                    "✅ Токен принят! Добро пожаловать в ОСИ Алматы!"
                )
            else:
                await message.answer(
                    "❌ Неверный токен приглашения.\n\n"
                    "Для получения доступа свяжитесь с администратором."
                )
                return
        else:
            # Показываем инструкцию
            if settings.ACCESS_MODE == "invite_only":
                await message.answer(
                    "👋 Добро пожаловать!\n\n"
                    "Для доступа к боту требуется токен приглашения.\n"
                    "Используйте команду: /start ВАШ_ТОКЕН\n\n"
                    "Или свяжитесь с администратором для получения доступа."
                )
                return
            elif settings.ACCESS_MODE == "whitelist":
                await message.answer(
                    "❌ Доступ к боту ограничен.\n\n"
                    "Для получения доступа свяжитесь с администратором."
                )
                return
    
    # Проверяем, выбран ли регион
    if not user.preferred_region_id:
        await message.answer(
            "👋 Добро пожаловать в ОСИ Алматы!\n\n"
            "Для начала работы, пожалуйста, выберите ваш регион:",
        )
        # Перенаправляем на выбор региона
        from app.bot.handlers.regions import show_regions
        await show_regions(message, session, user)
    else:
        await show_main_menu(message, user)


async def show_main_menu(message: Message, user: User):
    """Показать главное меню"""
    region_name = user.preferred_region.name if user.preferred_region else "Не выбран"
    
    text = (
        f"👋 Добро пожаловать, {h(user.first_name or 'пользователь')}!\n\n"
        f"📍 Ваш регион: {h(region_name)}\n\n"
        "Выберите действие:"
    )
    
    await message.answer(text, reply_markup=main_menu_keyboard())


@router.callback_query(F.data == "main_menu")
async def callback_main_menu(callback: CallbackQuery, user: User, state: FSMContext):
    """Возврат в главное меню"""
    # Выходим из режимов ввода (поиск, отзыв), чтобы следующий текст
    # не был воспринят как запрос/комментарий
    await state.set_state(None)
    region_name = user.preferred_region.name if user.preferred_region else "Не выбран"
    
    text = (
        f"👋 Главное меню\n\n"
        f"📍 Ваш регион: {h(region_name)}\n\n"
        "Выберите действие:"
    )
    
    await edit_or_send(callback.message, text, reply_markup=main_menu_keyboard())
    await callback.answer()


@router.callback_query(F.data == "noop")
async def callback_noop(callback: CallbackQuery):
    """Кнопки-индикаторы (номер страницы) — просто снимаем «часики»"""
    await callback.answer()

