import logging
import os
from rapidfuzz import process
import typing as tp
import psycopg
from psycopg.rows import dict_row
from dotenv import load_dotenv

logger = logging.getLogger("func")

load_dotenv()


async def get_connection() -> psycopg.AsyncConnection:
    """Establish database connection"""
    return await psycopg.AsyncConnection.connect(
        host=os.getenv("DB_HOST"),
        port=int(os.getenv("DB_PORT", 5432)),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD")
    )


async def get_some_reviews(place_id: str, review_limit: int) -> list[dict[str, tp.Any]] | None:
    """Fetch reviews for a place with ID"""
    conn = await get_connection()
    try:
        async with conn.cursor(row_factory=dict_row) as cur:
            await cur.execute('SELECT * FROM reviews WHERE place_id = %s LIMIT %s;', (str(place_id), review_limit))
            raw_reviews = await cur.fetchall()
            cooked_reviews = []
            for review in raw_reviews:
                await cur.execute('SELECT name FROM users WHERE id = %s;', (review['user_id'],))
                user_result = await cur.fetchone()
                review['author_name'] = user_result['name'] if user_result else "Anonymous"
                review['author_initials'] = await get_initials(review['author_name'])
                review['rating'] = review['score']
                review['text'] = review['feedback']
                review['generation_prob'] = review['llm_prob']
                review['relevance'] = None  # TODO: Calculate relevance

                # Cleanup unnecessary fields
                for field in ['score', 'place_id', 'user_id', 'inept_prob',
                              'bot_prob', 'llm_prob', 'spam_prob', 'corrected_score']:
                    if field in review:
                        del review[field]

                # Format date to ISO
                review['date'] = review['date'].isoformat().replace('+00:00', 'Z')
                cooked_reviews.append(review)
            return cooked_reviews
    except Exception as e:
        logger.error(f"Failed to fetch reviews: {str(e)}", exc_info=True)
    finally:
        await conn.close()


async def get_initials(name: str) -> str:
    """Generate user initials"""
    words = [word for word in name.strip().split() if not word.isdigit() and word]
    if not words:
        return "АН"
    initials = ''.join(word[0].upper() for word in words[:2])
    return initials if initials else "АН"


async def get_place_by_id(place_id: str, review_limit: int = 60) -> dict | None:
    """Get detailed place information by ID"""
    conn = await get_connection()
    try:
        async with conn.cursor(row_factory=dict_row) as cur:
            await cur.execute('SELECT * FROM places WHERE id = %s;', (place_id,))
            place_data = await cur.fetchone()
            if not place_data:
                return None

            # Get chain information
            await cur.execute('SELECT chain_size FROM chains WHERE id = %s;', (place_data['chain_id'],))
            chain_result = await cur.fetchone()
            place_data['chain_size'] = chain_result['chain_size'] if chain_result else 0
            del place_data['chain_id']

            # Calculate metrics
            # total_reviews = place_data['reviews_amout'] TODO ADD IN DB
            total_reviews = 0
            controversial_total = (
                    place_data['llm_amount'] +
                    place_data['bot_amount'] +
                    place_data['inept_amount']
            )

            place_data['total_reviews'] = total_reviews
            place_data['controversial_reviews'] = {
                'generated': place_data['llm_amount'],
                'bot': place_data['bot_amount'],
                'biased': place_data['inept_amount']
            }

            # Calculate percentages
            place_data['honest_percentage'] = round(
                ((total_reviews - controversial_total) / total_reviews * 100)
                if total_reviews else 0, 2
            )
            place_data['bot_percentage'] = round(
                (place_data['bot_amount'] / total_reviews * 100)
                if total_reviews else 0, 2
            )

            # Cleanup fields
            for field in ['llm_amount', 'bot_amount', 'spam_amount',
                          'inept_amount', 'reviews_amout']:
                if field == "reviews_amout":
                    continue               # TODO MAKE IT CORRECT
                del place_data[field]

            # Prepare ratings
            place_data['yandex_rating'] = place_data['rating']
            place_data['honest_rating'] = None  # TODO: Calculate from honest reviews
            place_data['honesty_rating'] = None  # TODO: Implement honesty rating

            # Get reviews
            place_data['reviews'] = await get_some_reviews(place_id, review_limit)
            return place_data
    except Exception as e:
        logger.error(f"Failed to get place by id: {str(e)}", exc_info=True)
    finally:
        await conn.close()


async def search_places_by_name(name_query: str, city: str = "Санкт-Петербург", limit: int = 10) -> list[dict] | None:
    """Search places by name with city filter"""
    conn = await get_connection()
    try:
        async with conn.cursor(row_factory=dict_row) as cur:
            # Get places in specified city
            await cur.execute('''
                SELECT id, name, address, rating, chain_id
                FROM places
                WHERE address ILIKE %s;
            ''', (f'%{city}%',))
            city_places = await cur.fetchall()

            # Get chain sizes in single query
            chain_ids = {p['chain_id'] for p in city_places if p['chain_id']}
            chain_sizes = {}
            if chain_ids:
                await cur.execute(
                    "SELECT id, chain_size FROM chains WHERE id = ANY(%s);",
                    (list(chain_ids),)
                )
                
                chain_sizes = {row['id']: row['chain_size'] for row in await cur.fetchall()}

            # Prepare places with chain sizes
            places_data = []
            for place in city_places:
                place_data = {
                    'id': place['id'],
                    'name': place['name'],
                    'address': place['address'],
                    'yandex_rating': place['rating'],
                    'chain_size': chain_sizes.get(place['chain_id'], 0),
                    'honesty_rating': None  # TODO: Implement
                }
                places_data.append(place_data)

            # Fuzzy matching
            place_names = [p['name'] for p in places_data]
            place_ids = [p['id'] for p in places_data]
            matches = process.extract(name_query, place_names, limit=limit)

            # Return matched results
            matched_places = []
            for match in matches:
                if match[1] < 30:  # Skip low score matches
                    continue
                for place in places_data:
                    if place['name'] == match[0] and place['id'] == place_ids[match[2]]:
                        matched_places.append(place)
                        break
            return matched_places
    except Exception as e:
        logger.error(f"Failed to search place by name: {str(e)}", exc_info=True)
    finally:
        await conn.close()


async def search_places_by_address(address: str, city: str = "Санкт-Петербург", limit: int = 10) -> list[dict]:
    """Search places by address (geospatial search not implemented)"""
    # TODO: Implement geocoding and distance calculation
    return []


async def get_place_details(place_id: str) -> dict | None:
    """Get detailed place information by ID """
    place_data = await get_place_by_id(place_id)
    if place_data:
        return place_data
    logger.debug(f"{place_id} did not found")
    return None


