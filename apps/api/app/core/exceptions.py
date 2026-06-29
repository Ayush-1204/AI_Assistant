class AppException(Exception):
    """Base exception for the application."""


class UserAlreadyExistsException(AppException):
    """Raised when a user with the given email already exists."""

class InvalidCredentialsException(AppException):
    """Raised when login credentials are invalid."""