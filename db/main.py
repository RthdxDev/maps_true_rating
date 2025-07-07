import db

if __name__ == "__main__":
    import sys
    import asyncio

    if sys.platform.startswith("win"):
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    # asyncio.run(db.upload_places())
    # asyncio.run(db.upload_reviews())
