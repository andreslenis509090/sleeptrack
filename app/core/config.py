"""Configuración de variables de entorno y cliente de Supabase (RNF04).

Carga automáticamente variables desde el archivo .env si está presente.
Provee fábrica de cliente Supabase para persistencia relacional en la nube.
"""

import os
from dataclasses import dataclass
from pathlib import Path
from dotenv import load_dotenv
from supabase import Client, create_client

# Cargar variables de entorno desde .env en la raíz del proyecto
BASE_DIR = Path(__file__).resolve().parent.parent.parent
ENV_FILE = BASE_DIR / ".env"
if ENV_FILE.exists():
    load_dotenv(dotenv_path=ENV_FILE)
else:
    load_dotenv()


@dataclass
class Settings:
    """Configuraciones del sistema SleepTrack."""

    api_prefix: str = os.getenv("API_PREFIX", "/api/v1")
    supabase_url: str = os.getenv("SUPABASE_URL", "")
    supabase_key: str = os.getenv("SUPABASE_KEY", "")
    environment: str = os.getenv("ENVIRONMENT", "development")
    testing: bool = os.getenv("TESTING", "").lower() in ("true", "1", "yes")

    @property
    def is_testing_mode(self) -> bool:
        """Determina si la aplicación se ejecuta explícitamente en modo de pruebas."""
        return self.testing or self.environment.lower() == "test"

    @property
    def is_supabase_configured(self) -> bool:
        """Verifica si las credenciales de Supabase están configuradas con valores válidos (no vacíos ni de ejemplo)."""
        url = (self.supabase_url or "").strip().lower()
        key = (self.supabase_key or "").strip().lower()

        if not url or not key:
            return False

        # Excluir valores de ejemplo / placeholder
        placeholders = [
            "mock-sleeptrack",
            "tu-proyecto",
            "mock-supabase-key",
            "tu-clave",
            "tu-anon",
            "your-project",
            "example.com",
        ]
        if any(p in url for p in placeholders) or any(p in key for p in placeholders):
            return False

        return url.startswith("http://") or url.startswith("https://")


settings = Settings()


def get_supabase_client() -> Client | None:
    """Crea y retorna un cliente de Supabase configurado, o None si no existen credenciales válidas."""
    if not settings.is_supabase_configured:
        return None

    url = settings.supabase_url.strip().rstrip("/")
    if url.endswith("/rest/v1"):
        url = url[:-len("/rest/v1")].rstrip("/")

    return create_client(url, settings.supabase_key.strip())
