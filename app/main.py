"""Punto de entrada de la aplicación FastAPI para SleepTrack (Backend).

Configura routers, middlewares, manejo estandarizado de excepciones y documentación OpenAPI.
"""

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from app.api.routers.auth_router import router as auth_router
from app.api.routers.sleep_records_router import router as sleep_records_router
from app.core.config import settings

app = FastAPI(
    title="SleepTrack API",
    description=(
        "API REST para el Sistema de Monitoreo de Higiene del Sueño.\n"
        "Dirigida a estudiantes y trabajadores con horarios irregulares.\n"
        "Persistencia relacional en la nube (Supabase / PostgreSQL).\n"
        "Autenticación con Supabase Auth (RF01, RF02, RNF01, RNF02)."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Estandariza los errores de validación de esquemas Pydantic v2 (RF06, HTTP 422)."""
    errors = exc.errors()
    first_error = errors[0] if errors else {}
    loc = first_error.get("loc", [])
    field_name = str(loc[-1]) if loc else None
    msg = first_error.get("msg", "Error de validación en la solicitud.")

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": msg,
                "field": field_name,
            }
        },
    )


# Registrar router del módulo de autenticación (RF01, RF02, RNF01, RNF02)
app.include_router(auth_router, prefix=settings.api_prefix)

# Registrar router del módulo de registros de sueño (HU1, RF03-RF09)
app.include_router(sleep_records_router, prefix=settings.api_prefix)


@app.get("/health", tags=["Health"])
def health_check():
    """Endpoint de estado del servicio."""
    return {"status": "ok", "service": "SleepTrack API"}
