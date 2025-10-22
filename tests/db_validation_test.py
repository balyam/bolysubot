"""
Тест для проверки ограничения длины комментария в отзывах
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import DataError
import sys
import os

# Добавляем корневую папку проекта в путь
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models import Base, Review, User, Contractor, Region


def test_review_comment_length_limit():
    """Тест ограничения длины комментария в 500 символов"""
    
    # Создаем тестовую базу данных в памяти
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Создаем тестовые данные
        region = Region(name="Тестовый регион")
        session.add(region)
        session.flush()
        
        contractor = Contractor(
            name="Тестовый исполнитель",
            phone="+1234567890",
            region_id=region.id
        )
        session.add(contractor)
        session.flush()
        
        user = User(
            telegram_id=12345,
            first_name="Тест",
            username="test_user"
        )
        session.add(user)
        session.flush()
        
        # Тест 1: Комментарий в пределах лимита (500 символов)
        short_comment = "A" * 500
        review1 = Review(
            contractor_id=contractor.id,
            user_id=user.id,
            user_name="Тест",
            rating=5,
            comment=short_comment
        )
        session.add(review1)
        session.commit()
        
        # Проверяем, что отзыв сохранился
        saved_review1 = session.query(Review).filter_by(id=review1.id).first()
        assert saved_review1.comment == short_comment
        assert len(saved_review1.comment) == 500
        
        # Тест 2: Попытка создать комментарий длиннее 500 символов
        long_comment = "A" * 501
        review2 = Review(
            contractor_id=contractor.id,
            user_id=user.id,
            user_name="Тест",
            rating=4,
            comment=long_comment
        )
        
        # Это должно вызвать ошибку базы данных
        try:
            session.add(review2)
            session.commit()
            print("❌ Ошибка: комментарий длиннее 500 символов был принят!")
            return False
        except (DataError, Exception) as e:
            print(f"✅ Ограничение работает: {type(e).__name__}")
            session.rollback()
        
        print("✅ Тест пройден: ограничение на 500 символов работает корректно")
        return True
        
    finally:
        session.close()


if __name__ == "__main__":
    success = test_review_comment_length_limit()
    if success:
        print("\n🎉 Все тесты прошли успешно!")
    else:
        print("\n❌ Тесты не прошли!")
        sys.exit(1)
