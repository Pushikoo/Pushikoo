"""Custom exceptions for Pushikoo application.

All service layer code should raise these exceptions instead of Python built-in exceptions.
Controller layer catches these and converts them to appropriate HTTP responses.
"""


class PushikooException(Exception):
    """Base exception for Pushikoo application."""

    pass


class NotFoundException(PushikooException):
    """Resource not found. Maps to HTTP 404."""

    pass


class ConflictException(PushikooException):
    """Resource conflict (e.g., already exists). Maps to HTTP 409."""

    pass


class InvalidInputException(PushikooException):
    """Invalid input or validation error. Maps to HTTP 400."""

    pass
