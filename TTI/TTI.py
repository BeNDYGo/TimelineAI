import random


def generate(prompt: str) -> str:
    """Возвращает случайное тестовое изображение"""
    images = [
        "output_7ae0c43b3ee54efba8ba21d9723e82ab.jpg",
        "output_f6a8d528f38a4a358bf7fcccdd58a080.jpg"
    ]
    
    return random.choice(images)
