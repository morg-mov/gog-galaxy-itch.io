"""Exceptions for the butler module."""


class BaseException(Exception):
    def __init__(self, message):
        """Base exception for Butler module. No real point calling this on it's own."""
        super().__init__(message)

class IncompatiblePlatform(BaseException):
    def __init__(self, message):
        """Raised when the given or detected platform is not in the list of supported platforms for Butler."""
        super().__init__(message)

class NotRunning(BaseException):
    def __init__(self, message):
        """Raised when a process-dependent function is called, but the Butler process has been closed."""
        super().__init__(message)

class SecretMissing(BaseException):
    def __init__(self, message, stdout):
        """Raised when client authentication secret could not be found in stdout."""
        super().__init__(message)
        self.stdout = stdout

class AuthenticationError(BaseException):
    def __init__(self, message, returned_msg, secret):
        super().__init__(message)
        self.returned_msg = returned_msg
        self.secret = secret