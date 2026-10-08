"""Configuración de variables de entorno y cliente de Supabase (RNF04)."""

import os
from dataclasses import dataclass
from supabase import Client, create_client


@dataclass
class Settings:
    """Configuraciones del sistema SleepTrack."""

    api_prefix: str = "/api/v1"
    supabase_url: str = os.getenv("SUPABASE_URL", "https://mock-sleeptrack.supabase.co")
    supabase_key: str = os.getenv("SUPABASE_KEY", "mock-supabase-key")
    environment: str = os.getenv("ENVIRONMENT", "development")


settings = Settings()


def get_supabase_client() -> Client:
    """Crea y retorna un cliente de Supabase configurado."""
    return create_client(settings.supabase_url, settings.supabase_key)
