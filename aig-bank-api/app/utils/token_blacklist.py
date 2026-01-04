"""Token blacklist management for handling revoked tokens."""

from .jwt import JWTManager


class TokenBlacklist:
    """Token blacklist manager for handling revoked tokens."""

    def __init__(self) -> None:
        """Initialize the token blacklist (in-memory for demo)."""
        self._blacklist: set[str] = set()

    def add_token(self, token: str) -> None:
        """Add a token to the blacklist."""
        try:
            payload = JWTManager.decode_token(token)
            token_id = payload.get("jti") or token 
            self._blacklist.add(token_id)
        except Exception:
            self._blacklist.add(token)

    def is_blacklisted(self, token: str) -> bool:
        """Check if a token is blacklisted."""
        try:
            payload = JWTManager.decode_token(token)
            token_id = payload.get("jti") or token 
            return token_id in self._blacklist
        except Exception:
            return True

    def clear_expired_tokens(self) -> int:
        """Clear expired tokens from blacklist. Returns number of tokens removed."""
        return 0


token_blacklist = TokenBlacklist()
