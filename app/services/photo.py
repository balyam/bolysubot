import aiofiles
from pathlib import Path
from typing import Optional
from aiogram import Bot
from aiogram.types import PhotoSize

from config import settings


async def save_photo(
    bot: Bot,
    photo: PhotoSize,
    contractor_id: int,
    filename: Optional[str] = None
) -> str:
    """
    Сохранить фото на диск
    
    Args:
        bot: Экземпляр бота
        photo: Объект фотографии
        contractor_id: ID исполнителя
        filename: Имя файла (если не указано, используется file_id)
    
    Returns:
        Путь к сохранённому файлу относительно PHOTOS_DIR
    """
    
    # Получаем информацию о файле
    file = await bot.get_file(photo.file_id)
    
    # Определяем имя файла
    if not filename:
        file_ext = file.file_path.split(".")[-1] if file.file_path else "jpg"
        filename = f"{photo.file_id}.{file_ext}"
    
    # Создаём путь к файлу
    contractor_dir = settings.photos_path / str(contractor_id)
    contractor_dir.mkdir(parents=True, exist_ok=True)
    
    file_path = contractor_dir / filename
    
    # Скачиваем и сохраняем файл
    await bot.download_file(file.file_path, file_path)
    
    # Возвращаем относительный путь
    return f"{contractor_id}/{filename}"


async def delete_photo(file_path: str) -> bool:
    """
    Удалить фото с диска
    
    Args:
        file_path: Относительный путь к файлу
    
    Returns:
        True если файл удалён, False если файл не существует
    """
    full_path = settings.photos_path / file_path
    
    if full_path.exists():
        full_path.unlink()
        return True
    
    return False

