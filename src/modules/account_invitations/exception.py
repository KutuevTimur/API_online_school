from src.modules.auth.exception import InvalidCredentials


class InvalidInvitation(InvalidCredentials):
    """Generic 401 for every invalid activation/recovery attempt."""
