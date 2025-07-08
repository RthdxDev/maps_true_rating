import os
from fuzzywuzzy import process
import typing as tp
from pathlib import Path
import json
import pprint
import psycopg
# pip install "psycopg[binary,async]"
from psycopg.rows import dict_row
from dotenv import load_dotenv

load_dotenv()
# TODO: Сделать функцию для отправки данных на фронт
# TODO: Подключить LLM api и api карт

# TODO: Удалить это нахуй, так как это для тестов (также удалить pprint)

pp = pprint.PrettyPrinter(indent=2)


# TODO: до сюда удалять

async def get_connection() -> psycopg.AsyncConnection:
    return await psycopg.AsyncConnection.connect(
        host=os.getenv("DB_HOST"),
        port=int(os.getenv("DB_PORT", 5432)),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD")
    )


async def get_some_reviews(place_id: str, review_limit: int) -> list[dict[str, tp.Any]]:
    conn = await get_connection()
    try:
        async with conn.cursor(row_factory=dict_row) as cur:
            await cur.execute('''
                SELECT * FROM reviews WHERE place_id = %s LIMIT %s;
            ''', (place_id, review_limit))
            raw_reviews = await cur.fetchall()
            cooked_reviews = []
            for review in raw_reviews:
                await cur.execute('''
                    SELECT name FROM users WHERE id = %s;
                ''', (review['user_id'],))
                review['author_name'] = (await cur.fetchone())['name']
                review['author_initials'] = await get_initials(review['author_name'])
                review['rating'] = review['score']
                del review['score']
                review['text'] = review['feedback']
                review['generation_prob'] = review['llm_prob']
                # TODO:
                review['relevance'] = await smth()
                del review['place_id']
                del review['user_id']
                del review['inept_prob']
                del review['bot_prob']
                del review['llm_prob']
                del review['spam_prob']
                del review['corrected_score']
                cooked_reviews.append(review)
            return cooked_reviews
    finally:
        await conn.close()


async def get_initials(name: str) -> str:
    words = [word for word in name.strip().split() if not word.isdigit()]
    if not words:
        return "X"
    initials = ''.join(word[0].upper() for word in words[:2] if word)
    return initials if initials else "X"


async def get_exact_place(place_id: str, review_limit: int = 0) -> dict[str, tp.Any]:
    conn = await get_connection()
    try:
        async with conn.cursor(row_factory=dict_row) as cur:
            await cur.execute('''
                SELECT * FROM places WHERE id = %s;
            ''', (place_id,))
            place_data = await cur.fetchone()
            await cur.execute('''
                SELECT chain_size FROM chains WHERE id = %s;
            ''', (place_data['chain_id'],))
            place_data['chain_size'] = (await cur.fetchone())['chain_size']
            del place_data['chain_id']
            place_data['total_reviews'] = place_data['reviews_amount']

            place_data['controversial_reviews'] = {
                'generated': place_data['llm_amount'],
                'bot': place_data['bot_amount'],
                'spam': place_data['spam_amount'],
                'biased': place_data['inept_amount']
            }
            place_data['honest_percentage'] = (place_data['llm_amount'] + place_data['bot_amount'] + place_data[
                'spam_amount'] + place_data['inept_amount']) / place_data['reviews_amount'] if place_data[
                                                                                                   'reviews_amount'] != 0 else 0 * 100
            place_data['bot_percentage'] = (place_data['bot_amount']) / place_data['reviews_amount'] if place_data[
                                                                                                            'reviews_amount'] != 0 else 0 * 100
            del place_data['llm_amount']
            del place_data['bot_amount']
            del place_data['spam_amount']
            del place_data['inept_amount']
            del place_data['reviews_amount']
            place_data['yandex_rating'] = place_data['rating']
            del place_data['rating']
            # TODO: Подсчёт честного рейтинга
            place_data['honest_rating'] = await smth()
            place_data['honesty_rating'] = await smth()
            place_data['reviews'] = await get_some_reviews(place_id, review_limit)
            return place_data
    finally:
        await conn.close()


async def get_some_places(text_name: str, limit: int):
    conn = await get_connection()
    try:
        async with conn.cursor() as cur:
            await cur.execute('''
                SELECT name, id FROM places;
            ''')
            raw_places = await cur.fetchall()
            search_base = [f"{word}||{id}" for word, id in raw_places]
            extraction_results = process.extract(text_name, search_base, limit=limit)
            best_matches = [match.split("||")[1] for match, score in extraction_results if score > 30]
            answer = []
            for match in best_matches:
                place_data = await get_exact_place(match)
                answer.append(place_data)
            pp.pprint(answer)
    finally:
        await conn.close()


async def smth(*args) -> tp.Any:
    pass


async def get_features(review_text: str) -> dict[str, float]:
    # TODO: Установите нормальное подключение к api
    features: list[float] = await smth(review_text)
    features = [0, 0, 0]
    LLM_feature: float = await smth(review_text)
    LLM_feature = 0
    return {'bot_prob': features[0],
            'spam_prob': features[1],
            'inept_prob': features[2],
            'LLM_prob': LLM_feature}


async def calculate_corrected_score(bot_prob: float, spam_prob: float, inept_prob: float, llm_prob: float,
                                    score: float) -> float:
    # TODO: Напишите формулу для исправленного балла или сделайте что-нибудь еще
    return score * (1 - (bot_prob + spam_prob + inept_prob + llm_prob) / 4.0)


async def add_review(review_data: dict[str, tp.Any]) -> None:
    conn = await get_connection()
    try:
        async with conn.cursor() as cur:
            place_id = review_data['place_id']
            try:
                await cur.execute('''
                    SELECT * FROM places WHERE id = %s;
                ''', (place_id,))
                place_info = await cur.fetchone()
                if place_info is None:
                    raise Exception(
                        f"Не существует такого места, данный отзыв пропущен, id: {review_data['review_id']}")
            except Exception as e:
                print(f'[LOG] {e}')
                return
            user_id = (await get_user(review_data['user_data']))['id']
            models_output = await get_features(review_data['feedback'])
            corrected_score = await calculate_corrected_score(models_output['bot_prob'], models_output['spam_prob'],
                                                              models_output['inept_prob'], models_output['LLM_prob'],
                                                              review_data['score'])
            try:
                await cur.execute('''
                    INSERT INTO reviews (
                        id, place_id, user_id, feedback, date, bot_prob, spam_prob, inept_prob,
                        LLM_prob, score, corrected_score
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
                ''', (
                    review_data['review_id'],
                    place_id,
                    user_id,
                    review_data['feedback'],
                    review_data['date'],
                    models_output['bot_prob'],
                    models_output['spam_prob'],
                    models_output['inept_prob'],
                    models_output['LLM_prob'],
                    review_data['score'],
                    corrected_score
                ))
            except Exception as e:
                print(f'[LOG] {e}')
            await conn.commit()
    finally:
        await conn.close()


# async def get_reviews(place_id: int) -> list[]

async def add_user(user_data: dict[str, tp.Any]) -> int:
    # TODO: Добавить подсчёт вероятности бота для юзера
    conn = await get_connection()
    try:
        async with conn.cursor() as cur:
            try:
                await cur.execute('''
                    INSERT INTO users (id, name, bad_reviews, good_reviews, total_reviews, probability_bad) VALUES (%s, %s, %s, %s, %s, %s);
                ''', (user_data['reviewer_id'], user_data['name'], 0, 0, user_data['total_reviews'], 0))
            except Exception as e:
                # Повторяющийся юзер
                print(f'[LOG] {e}')
            await conn.commit()
            return user_data['reviewer_id']
    finally:
        await conn.close()


async def add_chain(chain_name: str, chain_rating: float) -> int:
    conn = await get_connection()
    try:
        async with conn.cursor() as cur:
            await cur.execute('''
                INSERT INTO chains (name, chain_size, rating) VALUES (%s, %s, %s) RETURNING id;
            ''', (chain_name, 1, chain_rating))
            chain_id = (await cur.fetchone())[0]
            await conn.commit()
            return chain_id
    finally:
        await conn.close()


async def add_place(place_data: dict[str, tp.Any]) -> int:
    conn = await get_connection()
    try:
        async with conn.cursor() as cur:
            chain_id = (await get_chain(place_data['name'].lower(), place_data['rating']))['id']
            try:
                await cur.execute('''
                    INSERT INTO places (id, name, address, description, rating, chain_id, bot_amount, spam_amount, inept_amount, LLM_amount, reviews_amount) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
                ''', (place_data['place_id'], place_data['name'], place_data['address'], place_data['description'],
                      place_data['rating'], chain_id, 0, 0, 0, 0, 0))
            except Exception as e:
                # Нашли повторяющийся комментарий
                print(f'[LOG] {e}')
            await conn.commit()
            return place_data['place_id']
    finally:
        await conn.close()


# TODO: Добавить подсчет bad_reviews, good_reviews и probability_bad
async def get_user(user_data: dict[str, tp.Any]) -> dict[str, tp.Any]:
    conn = await get_connection()
    try:
        async with conn.cursor(row_factory=dict_row) as cur:
            await cur.execute('''
                SELECT * FROM users WHERE users.id = %s; 
            ''', (user_data['reviewer_id'],))
            user_information = await cur.fetchone()
            if user_information is None:
                user_id = await add_user(user_data)
                user_information = {'id': user_id,
                                    'name': user_data['name'],
                                    'bad_reviews': 0,
                                    'good_reviews': 0,
                                    'total_reviews': user_data['total_reviews'],
                                    'probability_bad': 0}
            else:
                await cur.execute('''
                    SELECT COUNT(*) FROM reviews WHERE user_id = %s AND 
                    (bot_prob > 0.7 OR spam_prob > 0.7 OR inept_prob > 0.7 OR LLM_prob > 0.7)
                ''', (user_data['reviewer_id'],))
                user_information['bad_reviews'] = (await cur.fetchone())['count']

                await cur.execute('''
                    SELECT COUNT(*) FROM reviews WHERE user_id = %s
                ''', (user_data['reviewer_id'],))
                user_information['good_reviews'] = (await cur.fetchone())['count'] - user_information['bad_reviews']

                await cur.execute('''
                    SELECT AVG((bot_prob + spam_prob + inept_prob + LLM_prob) / 4.0) FROM reviews WHERE id = %s;
                ''', (user_data['reviewer_id'],))
                # TODO: Формулка типо для всех prob берём среднее значение и дальше думаем, можно с весами сделать,
                # TODO: а можно че нибудь более умное
                user_avg = (await cur.fetchone())['avg']
                user_information['probability_bad'] = max(
                    (user_avg if user_avg else 0.0) * 1.2 - user_data['was_photo'] * 0.5, 0.0)

                await cur.execute('''
                    UPDATE users SET bad_reviews = %s, good_reviews = %s, probability_bad = %s WHERE id = %s;
                ''', (
                    user_information['bad_reviews'], user_information['good_reviews'],
                    user_information['probability_bad'],
                    user_data['reviewer_id']))
            return user_information
    finally:
        await conn.close()


async def get_chain(chain_name: str, chain_rating: int = 0) -> dict[str, tp.Any]:
    conn = await get_connection()
    try:
        async with conn.cursor(row_factory=dict_row) as cur:
            await cur.execute('''
                SELECT * FROM chains WHERE chains.name = %s;
            ''', (chain_name,))
            chain_information = await cur.fetchone()
            if chain_information is None:
                chain_id = await add_chain(chain_name, chain_rating)
                chain_information = {'id': chain_id,
                                     'name': chain_name,
                                     'chain_size': 1,
                                     'rating': 0}
            else:
                await cur.execute('''
                    SELECT COUNT(*) FROM places WHERE chain_id = %s;
                ''', (chain_information['id'],))
                chain_information['chain_size'] = (await cur.fetchone())['count']

                await cur.execute('''
                    UPDATE chains SET chain_size = %s WHERE id = %s;
                ''', (chain_information['chain_size'], chain_information['id']))

                await cur.execute('''
                    SELECT AVG(rating) FROM places WHERE chain_id = %s;
                ''', (chain_information['id'],))
                chain_information['rating'] = (await cur.fetchone())['avg']

                await cur.execute('''
                    UPDATE chains SET rating = %s WHERE id = %s;
                ''', (chain_information['rating'], chain_information['id']))
                await conn.commit()
            return chain_information
    finally:
        await conn.close()


# TODO: сделать АДЕКВАТНЫЙ подсчёт amount-ов (пока что все что prob > 0.7 это подходит под критерий

async def get_place(place_data: dict[str, tp.Any]) -> dict[str, tp.Any]:
    conn = await get_connection()
    try:
        async with conn.cursor(row_factory=dict_row) as cur:
            await cur.execute('''
                SELECT * FROM places WHERE places.id = %s;
            ''', (place_data['place_id'],))
            place_information = await cur.fetchone()
            if place_information is None:
                place_id = await add_place(place_data)
                place_information = {'id': place_id,
                                     'name': place_data['name'],
                                     'address': place_data['address'],
                                     'description': place_data['description'],
                                     'rating': place_data['rating'],
                                     'chain_id': (await get_chain(place_data['place_name'], place_data['rating'])),
                                     'bot_amount': 0,
                                     'spam_amount': 0,
                                     'inept_amount': 0,
                                     'LLM_amount': 0,
                                     'reviews_amount': 0,
                                     }
            else:
                # TODO: Придумать как пересчитывать amount's
                # Общее количество
                await cur.execute('''
                    SELECT COUNT(*) FROM reviews WHERE place_id = %s;
                ''', (place_data['place_id'],))
                place_data['reviews_amount'] = (await cur.fetchone())['count']

                await cur.execute('''
                    UPDATE places SET reviews_amount = %s WHERE id = %s;
                ''', (place_data['reviews_amount'], place_data['place_id']))
                # Количество комментариев от ботов
                await cur.execute('''
                    SELECT COUNT(*) FROM reviews WHERE place_id = %s AND bot_prob > 0.7
                ''', place_data['place_id'])
                place_data['bot_amount'] = (await cur.fetchone())['count']

                await cur.execute('''
                    UPDATE places SET reviews_amount = %s WHERE id = %s;
                ''', (place_data['bot_amount'], place_data['place_id']))
                # Количество комментариев от спамеров
                await cur.execute('''
                    SELECT COUNT(*) FROM reviews WHERE place_id = %s AND spam_prob > 0.7
                ''', place_data['place_id'])
                place_data['spam_amount'] = (await cur.fetchone())['count']

                await cur.execute('''
                    UPDATE places SET spam_amount = %s WHERE id = %s;
                ''', (place_data['spam_amount'], place_data['place_id']))
                # Количество комментариев от необразованных
                await cur.execute('''
                    SELECT COUNT(*) FROM reviews WHERE place_id = %s AND inept_prob > 0.7
                ''', place_data['place_id'])
                place_data['inept_amount'] = (await cur.fetchone())['count']

                await cur.execute('''
                    UPDATE places SET inept_amount = %s WHERE id = %s;
                ''', (place_data['inept_amount'], place_data['place_id']))
                # Количество комментариев от LLM
                await cur.execute('''
                    SELECT COUNT(*) FROM reviews WHERE place_id = %s AND LLM_prob > 0.7
                ''', place_data['place_id'])
                place_data['LLM_amount'] = (await cur.fetchone())['count']

                await cur.execute('''
                    UPDATE places SET LLM_amount = %s WHERE id = %s;
                ''', (place_data['LLM_amount'], place_data['place_id']))
            return place_information
    finally:
        await conn.close()


async def upload_places(path_to_file: Path = None):
    if path_to_file is None:
        current_dir = os.path.dirname(__file__)
        json_path = os.path.join(current_dir, '..', 'datapack', 'places.json')
        path_to_file = os.path.abspath(json_path)
    with open(path_to_file, 'r', encoding='utf-8') as file:
        data = json.load(file)
    for place_data in data:
        await add_place(place_data)


async def upload_reviews(path_to_file: Path = None):
    if path_to_file is None:
        current_dir = os.path.dirname(__file__)
        json_path = os.path.join(current_dir, '..', 'datapack', 'reviews.json')
        path_to_file = os.path.abspath(json_path)
    with open(path_to_file, 'r', encoding='utf-8') as file:
        data = json.load(file)
    for raw_review_data in data:
        review_data = {
            'place_id': raw_review_data['place_id'],
            'review_id': raw_review_data['review_id'],
            'user_data': {
                'name': raw_review_data['name'],
                'reviewer_id': str(raw_review_data['reviewer_id']),
                'total_reviews': raw_review_data['total_reviews'],
                'was_photo': raw_review_data['was_photo']
            },
            'date': raw_review_data['date'],
            'score': raw_review_data['score'],
            'feedback': raw_review_data['feedback']
        }
        await add_review(review_data)


async def print_tables():
    conn = await get_connection()
    try:
        async with conn.cursor(row_factory=dict_row) as cur:
            await cur.execute('''
                SELECT * FROM places;
            ''')
            place_data = await cur.fetchall()
            print('PLACES:    ')
            pp.pprint(place_data)
            await cur.execute('''
                SELECT * FROM users;
            ''')
            users_data = await cur.fetchall()
            print('USERS:     ')
            pp.pprint(users_data)
            await cur.execute('''
                SELECT * FROM chains;
            ''')
            chain_data = await cur.fetchall()
            print('CHAINS:     ')
            pp.pprint(chain_data)
            await cur.execute('''
                SELECT * FROM reviews;
            ''')
            review_data = await cur.fetchall()
            print('Reviews:     ')
            pp.pprint(review_data)
    finally:
        await conn.close()


if __name__ == "__main__":
    import sys
    import asyncio

    if sys.platform.startswith("win"):
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(print_tables())
