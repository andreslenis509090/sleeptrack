"""Routers de FastAPI para los módulos de SleepTrack."""

from app.api.routers.sleep_records_router import router as sleep_records_router

__all__ = ["sleep_records_router"]
