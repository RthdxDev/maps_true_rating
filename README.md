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
# Backend Deployment to Yandex Cloud

#### Create Container Registry
```bash
yc container registry create --name honest-reviews-registry
```

#### Build and Push Docker Image
```bash
docker build -t honest-reviews-api ./backend
yc container registry configure-docker
docker tag honest-reviews-api cr.yandex/<registry-id>/honest-reviews-api:1.0
docker push cr.yandex/<registry-id>/honest-reviews-api:1.0
```

#### Create Serverless Container
```bash
yc serverless container create --name honest-reviews-container
```

#### Configure Container
```bash
yc serverless container revision deploy \
  --container-name honest-reviews-container \
  --image cr.yandex/<registry-id>/honest-reviews-api:1.0 \
  --cores 1 \
  --memory 1024MB \
  --concurrency 100 \
  --environment DB_HOST=<host>,DB_PORT=5432,DB_NAME=<db>,DB_USER=<user>,DB_PASSWORD=<pass>
```

#### Create API Gateway
`gateway.yaml`:
```yaml
openapi: 3.0.0
info:
  title: Honest Reviews API
  version: 1.0.0
servers:
- url: https://<container-id>.yandexcloud.net
paths:
  /places/search:
    get:
      summary: Search places by name
      operationId: searchByName
      parameters:
        - name: name
          in: query
          required: true
          schema:
            type: string
        - name: city
          in: query
          required: false
          schema:
            type: string
      x-yc-apigateway-integration:
        type: serverless_containers
        container_id: <container-id>
        service_account_id: <service-account-id>  
  /places/detail:
    get:
      summary: Get place details
      operationId: getPlaceDetails
      parameters:
        - name: place_id
          in: query
          required: true
          schema:
            type: string
      x-yc-apigateway-integration:
        type: serverless_containers
        container_id: <container-id>
        service_account_id: <service-account-id>
```

## Configuration Reference

### Environment Variables
| Variable | Description | Default |
|----------|-------------|---------|
| `DB_HOST` | PostgreSQL host | - |
| `DB_PORT` | PostgreSQL port | `5432` |
| `DB_NAME` | Database name | - |
| `DB_USER` | Database user | - |
| `DB_PASSWORD` | Database password | - |
| `LOG_LEVEL` | Logging verbosity | `INFO` |

### API Endpoints
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/v1/places/search` | GET | Search places by name |
| `/v1/places/detail` | GET | Get place details by ID |

## Honest Rating Calculation
The system calculates honest ratings using:

```python
relevance = (1 - llm_prob/4) * (1 - inept_prob/2) * (1 - spam_prob/5)
honest_rating = Σ(review_rating * relevance) / Σ(relevance)
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