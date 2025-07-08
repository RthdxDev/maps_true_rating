 # Асинхронный модуль работы с PostgreSQL отзывами и заведениями
 
 Этот модуль предоставляет асинхронный API для работы с базой данных PostgreSQL, содержащей информацию о заведениях, отзывах, пользователях и сетях. Реализованы функции добавления, выборки, фильтрации и загрузки данных из JSON-файлов.
 
 ---
 
 ## 🔧 Требования
 
 - Python 3.10+
 - PostgreSQL
 - Установленные зависимости:
 
 ```bash
 pip install -r requirements.txt
 ```

 ---
 
 ## 📁 Структура проекта
 
 - `db.py` — основной модуль для работы с БД.
 - `datapack/places.json` — файл с заведениями.
 - `datapack/reviews.json` — файл с отзывами.
 - `.env` — переменные окружения для подключения к БД.
 
 ---

 ## 📌 Основные функции
 
 ### Заведения
 
 - `add_place(place_data: dict) -> str` — добавляет заведение.
 - `get_place(place_data: dict) -> dict` — возвращает полную информацию о заведении.
 - `get_exact_place(place_id: str, review_limit=0) -> str` — информация + отзывы (JSON).
 - `get_some_places(text_name: str, limit: int) -> str` — fuzzy-поиск заведений по названию.
 
 ### Отзывы
 
 - `add_review(review_data: dict)` — добавляет отзыв.
 - `get_used_reviews() -> list[str]` — возвращает ID добавленных отзывов.
 - `get_some_reviews(place_id: str, review_limit: int)` — получить отзывы по заведению.
 
 ### Пользователи
 
 - `add_user(user_data: dict) -> str` — добавляет пользователя.
 - `get_user(user_data: dict) -> dict` — получает или добавляет пользователя.
 
 ### Сети заведений
 
 - `add_chain(chain_name: str, rating: float) -> int` — добавляет новую сеть.
 - `get_chain(chain_name: str, rating: float) -> dict` — получить информацию о сети.
 
 ### Загрузка данных
 
 - `upload_places(path_to_file: Path = None)` — загружает заведения из JSON-файла.
 - `upload_reviews(path_to_file: Path = None)` — загружает отзывы из JSON-файла.
 
 Если `path_to_file` не указан, будет использоваться `../datapack/places.json` или `../datapack/reviews.json`.
 
 ---
 
 ## 🧪 Отладка и тесты
 
 - `drop_tables()` — удаляет все таблицы (для отладки).
 - `print_tables()` — печатает содержимое всех таблиц.
 
 ---
 
 ## 🚀 Пример использования
 
 ```python
 import asyncio
 from db import get_some_places
 
 async def main():
     data = await get_some_places("Пятёрочка", limit=5)
     print(data)
 
 asyncio.run(main())
 ```
 
 ---
 
 ## 🧠 Заметки разработчика
 
 - Некоторые функции используют заглушки (`await smth()`), их нужно реализовать.
 - Часть логики требует доработки (например, честный рейтинг, корректировки вероятностей).
 - Для анализа используется `fuzzywuzzy`, но можно заменить на `rapidfuzz` для скорости.
 - Модуль рассчитан на асинхронную работу, запуск синхронно приведёт к ошибкам.
