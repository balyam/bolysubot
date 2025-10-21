from aiogram import Router
from app.bot.handlers import start, search, categories, regions, contractor, reviews

# Главный роутер для всех хендлеров
main_router = Router()

# Подключаем все роутеры
main_router.include_router(start.router)
main_router.include_router(regions.router)
main_router.include_router(categories.router)
main_router.include_router(search.router)
main_router.include_router(contractor.router)
main_router.include_router(reviews.router)

__all__ = ["main_router"]

