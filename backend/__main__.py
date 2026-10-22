"""Run the local gateway using the same settings as the frontend proxy."""
import uvicorn

from backend.config import settings

if __name__ == "__main__":
    uvicorn.run(
        "backend.main:app", host=settings.APP_HOST, port=settings.APP_PORT,
        reload=settings.APP_ENV.lower() == "development",
    )
