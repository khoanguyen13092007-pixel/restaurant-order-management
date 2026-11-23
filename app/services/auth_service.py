"""NV1 - Login business logic (use case Login)."""
from app.repositories.user_repository import UserRepository


class AuthError(Exception):
    """Login error; the message can be shown to the user."""


class AuthService:
    def __init__(self, users=None):
        self.users = users or UserRepository()

    def authenticate(self, username, password):
        username = (username or "").strip()
        if not username or not password:
            raise AuthError("Please enter your username and password.")
        user = self.users.find_by_username(username)
        # Same message for unknown user and wrong password so accounts are not revealed
        if user is None or not user.check_password(password):
            raise AuthError("Invalid username or password.")
        if not user.is_active:
            raise AuthError("This account is disabled.")
        return user
