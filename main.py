import logging
import os
import sys
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from func import search_places_by_name, get_place_details
from typing import List, AsyncGenerator

# Configure root logger
root_logger = logging.getLogger()
for handler in root_logger.handlers[:]:
    root_logger.removeHandler(handler)
    handler.close()

root_logger.setLevel(logging.DEBUG)

console_handler = logging.StreamHandler(sys.stdout)
file_handler = logging.FileHandler('api.log', mode='a', encoding='utf-8')

console_handler.setLevel(logging.INFO)
file_handler.setLevel(logging.DEBUG)

log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
formatter = logging.Formatter(log_format)
console_handler.setFormatter(formatter)
file_handler.setFormatter(formatter)

root_logger.addHandler(console_handler)
root_logger.addHandler(file_handler)

logger = logging.getLogger("main")
func_logger = logging.getLogger("func")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # Startup code
    logger.info("Starting API server")
    logger.info(f"Environment: {os.getenv('ENV', 'development')}")
    logger.info(f"Database host: {os.getenv('DB_HOST', 'localhost')}")
    logger.debug("Debug mode enabled - verbose logging active")

    logger.debug("DEBUG test message - should appear in file")
    logger.info("INFO test message - should appear everywhere")

    yield  # App runs here

    logger.info("Stopping API server")
    # Add any cleanup logic here


app = FastAPI(lifespan=lifespan)


@app.get("/places/search", response_model=List[dict])
async def search_by_name(
        name: str,
        city: str = "Санкт-Петербург"
):
    logger.debug(f"Search by name initiated - Name: '{name}', City: '{city}'")
    try:
        results = await search_places_by_name(name, city, limit=10)
        logger.info(f"Search by name completed - Found {len(results)} results")
        return results
    except Exception as e:
        logger.error(f"Search by name failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/places/nearby", response_model=List[dict])
async def search_by_address(
        address: str,
        city: str = "Санкт-Петербург",
        limit: int = 10
):
    logger.info(f"Search by address initiated - Address: '{address}', City: '{city}'")
    # TODO: Implement geocoding and distance calculation
    logger.warning("Search by address endpoint called but not implemented")
    return []


@app.get("/places/detail", response_model=dict)
async def get_place(place_id: str):
    logger.info(f"Get place details initiated - Place ID: '{place_id}'")
    try:
        place_data = await get_place_details(place_id)
        if not place_data:
            logger.warning(f"Place not found: {place_id}")
            raise HTTPException(status_code=404, detail="Place not found")

        logger.info(f"Place details retrieved successfully: {place_id}")
        return place_data
    except Exception as e:
        logger.error(f"Failed to get place details: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        lifespan="on",
        log_level="debug"
    )
