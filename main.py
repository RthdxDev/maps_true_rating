import logging
import os
import sys
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from func import search_places_by_name, get_place_details
from typing import List

# Clear any existing loggers
logging.basicConfig(level=logging.DEBUG)
root_logger = logging.getLogger()
for handler in root_logger.handlers[:]:
    root_logger.removeHandler(handler)
    handler.close()

root_logger.setLevel(logging.DEBUG)

console_handler = logging.StreamHandler(sys.stdout)
file_handler = logging.FileHandler('api.log', mode='a', encoding='utf-8')

# Set handler levels
console_handler.setLevel(logging.INFO)
file_handler.setLevel(logging.DEBUG)

log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
formatter = logging.Formatter(log_format)
console_handler.setFormatter(formatter)
file_handler.setFormatter(formatter)

# Add handlers to root logger
root_logger.addHandler(console_handler)
root_logger.addHandler(file_handler)

# Get module-specific loggers
logger = logging.getLogger("main")
func_logger = logging.getLogger("func")

app = FastAPI()
# Add CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)


@app.on_event("startup")
async def startup_event():
    logger.info("Starting API server")
    logger.info(f"Environment: {os.getenv('ENV', 'development')}")
    logger.info(f"Database host: {os.getenv('DB_HOST', 'localhost')}")


@app.get("/v1/places/search", response_model=List[dict])
async def search_by_name(
    name: str,
    city: str = "Санкт-Петербург"
):
    logger.debug(f"SEARCH---- {name}")
    results = await search_places_by_name(name, city, limit=10)
    return results


@app.get("/v1/places/nearby", response_model=List[dict])
async def search_by_address(
    address: str,
    city: str = "Санкт-Петербург",
    limit: int = 10
):
    # TODO: Implement geocoding and distance calculation
    return []


@app.get("/v1/places/detail", response_model=dict)
async def get_place(place_id: str):
    logger.info("Hello!!!")
    place_data = await get_place_details(place_id)
    if not place_data:
        logger.error(f"Failed to get place details: {place_id}", exc_info=True)
        raise HTTPException(status_code=404, detail="Place not found")
    logger.error(f"Failed to get place details: {place_id}", exc_info=True)
    return place_data


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Stopping API server")


@app.get("/test-logging")
async def test_logging():
    """Endpoint to test logging functionality"""
    logger.debug("This is a DEBUG message - should only appear in log file")
    logger.info("This is an INFO message - should appear everywhere")
    logger.warning("This is a WARNING message - should appear everywhere")
    logger.error("This is an ERROR message - should appear everywhere")

    # Also test func logger
    func_logger.debug("Func DEBUG test")
    func_logger.info("Func INFO test")

    return {
        "status": "Logging test complete",
        "message": "Check console and api.log for output"
    }
