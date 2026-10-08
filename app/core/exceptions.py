"""Jerarquía de excepciones de dominio para SleepTrack.

Cumple con la separación de responsabilidades: la capa de servicio lanza estas
excepciones de dominio, las cuales son traducidas en la capa router a códigos HTTP.
"""


class DomainError(Exception):
    """Excepción base para errores de la lógica de dominio."""

    def __init__(self, message: str, code: str = "DOMAIN_ERROR") -> None:
        super().__init__(message)
        self.message = message
        self.code = code


class SleepRecordAlreadyExistsError(DomainError):
    """Lanzada cuando se intenta registrar un evento de sueño duplicado en una misma fecha (RN01).

    Permite al cliente móvil redirigir al flujo de edición (RF08).
    """

    def __init__(
        self,
        message: str = "Ya existe un registro de sueño para esta fecha. Utilice la opción de edición (RF08).",
        existing_record_id: int | None = None,
    ) -> None:
        super().__init__(message, code="RECORD_ALREADY_EXISTS")
        self.existing_record_id = existing_record_id


class FutureSleepTimeError(DomainError):
    """Lanzada cuando la hora de inicio de sueño es posterior a la hora actual (RN02)."""

    def __init__(
        self,
        message: str = "No se puede registrar una hora de inicio de sueño en el futuro.",
    ) -> None:
        super().__init__(message, code="FUTURE_TIME_NOT_ALLOWED")


class SleepRecordNotFoundError(DomainError):
    """Lanzada cuando un registro de sueño solicitado no existe."""

    def __init__(self, message: str = "Registro de sueño no encontrado.") -> None:
        super().__init__(message, code="RECORD_NOT_FOUND")


class InvalidSleepDataError(DomainError):
    """Lanzada cuando los datos de registro de sueño violan restricciones del dominio (RF06)."""

    def __init__(self, message: str, field: str | None = None) -> None:
        super().__init__(message, code="INVALID_SLEEP_DATA")
        self.field = field


class AuthenticationError(DomainError):
    """Lanzada cuando las credenciales de autenticación son inválidas (RF02)."""

    def __init__(
        self,
        message: str = "Correo o contraseña incorrectos.",
    ) -> None:
        super().__init__(message, code="INVALID_CREDENTIALS")


class UserAlreadyExistsError(DomainError):
    """Lanzada cuando el correo ya está registrado (RF01)."""

    def __init__(
        self,
        message: str = "Ya existe un usuario registrado con este correo electrónico.",
    ) -> None:
        super().__init__(message, code="USER_ALREADY_EXISTS")


class InvalidTokenError(DomainError):
    """Lanzada cuando el token de sesión es inválido o ha expirado (RNF02)."""

    def __init__(
        self,
        message: str = "Token de sesión inválido o expirado.",
    ) -> None:
        super().__init__(message, code="INVALID_TOKEN")
