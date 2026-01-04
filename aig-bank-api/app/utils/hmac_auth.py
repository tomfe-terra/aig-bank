"""HMAC-based authentication utilities for API key verification.

Implements HMAC signature chain to prevent replay attacks:
1. OperationKey: HMAC(secret, method + uri) - prevents method/URI modification
2. Final signature: HMAC(OperationKey, body) - prevents body modification
"""

import base64
import hashlib
import hmac

from fastapi import Request


class HMACAuthenticator:
    """Handles HMAC signature verification for API key authentication.

    Signature scheme:
    - Authorization header: "aigsignature {api_key_id}"
    - Signature header: base64(HMAC-chain-digest)
    - Chain: HMAC(HMAC(secret, method+uri), body)
    """

    @staticmethod
    def extract_headers(request: Request) -> tuple[str | None, str | None]:
        """Extract authentication headers from request.

        Args:
            request: FastAPI Request object

        Returns:
            Tuple of (api_key_id, signature) or (None, None) if headers are missing
        """
        auth_header = request.headers.get("Authorization")
        api_key_id = None
        if auth_header and auth_header.startswith("aigsignature "):
            api_key_id = auth_header[13:]

        signature = request.headers.get("Signature")

        return api_key_id, signature

    @staticmethod
    def compute_signature(secret: str, method: str, uri: str, body: bytes | None = None) -> str:
        """Compute HMAC signature using signature chain.

        Signature chain prevents replay attacks:
        1. OperationKey = HMAC(secret, method + uri)
        2. Final = HMAC(OperationKey, body)

        Args:
            secret: API key secret
            method: HTTP method (GET, POST, etc.)
            uri: Request URI/path
            body: Optional request body bytes

        Returns:
            Base64-encoded signature
        """
        digester = hmac.new(secret.encode(), None, hashlib.sha256)
        digester.update(f"{method}{uri}".encode())

        digester = hmac.new(digester.digest(), None, hashlib.sha256)
        if body is not None:
            digester.update(body)

        return base64.b64encode(digester.digest()).decode()

    @staticmethod
    def verify_signature(expected: str, provided: str) -> bool:
        """Verify signature using constant-time comparison.

        Args:
            expected: Expected signature (base64)
            provided: Provided signature from client (base64)

        Returns:
            True if signatures match, False otherwise
        """
        return hmac.compare_digest(expected, provided)

    @classmethod
    async def verify_request(cls, request: Request, secret: str) -> bool:
        """Verify HMAC signature for a request.

        Args:
            request: FastAPI Request object
            secret: API key secret

        Returns:
            True if signature is valid, False otherwise
        """
        _, provided_signature = cls.extract_headers(request)
        if not provided_signature:
            return False

        try:
            body = await request.body()
        except Exception:
            body = b""

        expected_signature = cls.compute_signature(
            secret=secret,
            method=request.method,
            uri=request.url.path,
            body=body if body else None,
        )

        return cls.verify_signature(expected_signature, provided_signature)
