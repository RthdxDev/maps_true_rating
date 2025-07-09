# Honest Reviews API

## Overview
The Honest Reviews API provides a backend service for analyzing and presenting establishment reviews with integrity verification. It enables users to search for places by name in Saint Petersburg and retrieve detailed information including review analysis, ratings, and authenticity metrics.

## Key Features
- Search establishments by name
- Retrieve detailed place information
- Analyze review authenticity and reliability
- Calculate honesty ratings
- Provide review metadata (bot probability, relevance)

## API Endpoints

### 1. Search by Name
**Endpoint**: `GET /v1/places/search`  
**Parameters**:
- `name` (required): Establishment name
- `city` (optional, default: "Санкт-Петербург"): City filter

**Example Request**:
```bash
curl "https://api.chestnye-otzyvy.ru/v1/places/search?name=Coffee&city=Санкт-Петербург"
```

**Example Response**:
```json
[
  {
    "id": "place_123",
    "name": "Coffee House",
    "chain_size": 5,
    "address": "10 Nevsky Prospekt, Санкт-Петербург",
    "yandex_rating": 4.7,
    "honesty_rating": 8.2
  },
  {
    "id": "place_456",
    "name": "Coffee Lab",
    "chain_size": 2,
    "address": "25 Liteyny Prospekt, Санкт-Петербург",
    "yandex_rating": 4.5,
    "honesty_rating": 7.8
  }
]
```

### 2. Get Place Details
**Endpoint**: `GET /v1/places/detail`  
**Parameters**:
- `place_id` (required): Establishment ID in `place_<number>` format

**Example Request**:
```bash
curl "https://api.chestnye-otzyvy.ru/v1/places/detail?place_id=place_123"
```

**Example Response**:
```json
{
  "id": "place_123",
  "name": "Coffee House",
  "chain_size": 5,
  "address": "10 Nevsky Prospekt, Санкт-Петербург",
  "total_reviews": 347,
  "controversial_reviews": {
    "generated": 52,
    "bot": 35,
    "biased": 17
  },
  "honest_percentage": 70.0,
  "bot_percentage": 10.1,
  "yandex_rating": 4.7,
  "honest_rating": 4.5,
  "honesty_rating": 8.2,
  "reviews": [
    {
      "id": "rev_001",
      "author_name": "Иван Петров",
      "author_initials": "ИП",
      "date": "2023-05-15T12:30:00Z",
      "rating": 4.5,
      "text": "Отличный кофе и атмосфера...",
      "generation_prob": 12.3,
      "relevance": 92
    }
  ]
}
```

## Technologies Used
- **Framework**: FastAPI (Python)
- **Database**: PostgreSQL
- **Deployment**: Yandex Cloud Serverless Containers
- **API Gateway**: Yandex API Gateway
- **Libraries**:
  - psycopg (PostgreSQL adapter)
  - python-dotenv (environment management)
  - rapidfuzz (fuzzy string matching)


## Support
Not Support.