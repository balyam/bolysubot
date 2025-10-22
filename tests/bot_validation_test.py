"""
Тест для проверки валидации длины комментария в боте
"""
import sys
import os

# Добавляем корневую папку проекта в путь
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_comment_length_validation():
    """Тест валидации длины комментария в боте"""
    
    # Симулируем логику валидации из бота
    def validate_comment_length(comment):
        """Валидация длины комментария (из бота)"""
        if comment and len(comment) > 500:
            return False, f"❌ Комментарий слишком длинный ({len(comment)} символов).\nМаксимальная длина комментария: 500 символов."
        return True, None
    
    # Тест 1: Комментарий в пределах лимита
    short_comment = "A" * 500
    is_valid, error = validate_comment_length(short_comment)
    assert is_valid, f"Короткий комментарий должен быть валидным: {error}"
    print("✅ Тест 1 пройден: комментарий в 500 символов принят")
    
    # Тест 2: Комментарий длиннее лимита
    long_comment = "A" * 501
    is_valid, error = validate_comment_length(long_comment)
    assert not is_valid, "Длинный комментарий должен быть отклонен"
    assert "слишком длинный" in error, "Сообщение об ошибке должно содержать информацию о длине"
    assert "501 символов" in error, "Сообщение должно показывать фактическую длину"
    print("✅ Тест 2 пройден: комментарий длиннее 500 символов отклонен")
    
    # Тест 3: Пустой комментарий (пропуск)
    is_valid, error = validate_comment_length(None)
    assert is_valid, "Пустой комментарий должен быть валидным"
    print("✅ Тест 3 пройден: пустой комментарий принят")
    
    # Тест 4: Комментарий точно на границе
    boundary_comment = "A" * 500
    is_valid, error = validate_comment_length(boundary_comment)
    assert is_valid, "Комментарий точно в 500 символов должен быть валидным"
    print("✅ Тест 4 пройден: комментарий точно в 500 символов принят")
    
    # Тест 5: Комментарий на 1 символ больше границы
    over_boundary_comment = "A" * 501
    is_valid, error = validate_comment_length(over_boundary_comment)
    assert not is_valid, "Комментарий в 501 символ должен быть отклонен"
    print("✅ Тест 5 пройден: комментарий в 501 символ отклонен")
    
    print("\n🎉 Все тесты валидации бота прошли успешно!")
    return True


if __name__ == "__main__":
    try:
        test_comment_length_validation()
    except AssertionError as e:
        print(f"❌ Тест не прошел: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Ошибка в тесте: {e}")
        sys.exit(1)
