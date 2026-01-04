"""Middleware configuration for CORS, trusted hosts, and request tracking."""

from collections.abc import Callable, Iterable
import json
import logging
import secrets

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware


class FormToJSONMiddleware:
    """ASGI middleware that converts form-encoded requests to JSON.

    For POST/PUT/PATCH:
      - If Content-Type is application/x-www-form-urlencoded,
      - Convert the body to JSON and switch Content-Type to application/json.

    This lets endpoints that expect Pydantic JSON bodies also accept forms globally.
    """

    def __init__(
        self,
        app,
        *,
        methods: Iterable[str] = ("POST", "PUT", "PATCH"),
        merge_json_fields: Iterable[str] = ("payload", "data", "user", "user_data"),
        path_predicate: Callable[[str], bool] | None = None,
    ):
        """Initialize the middleware.

        Args:
            app: The ASGI application
            methods: HTTP methods to process
            merge_json_fields: Field names to merge if they contain JSON strings
            path_predicate: Function to determine if a path should be processed
        """
        self.app = app
        self.methods = {m.upper() for m in methods}
        self.merge_json_fields = set(merge_json_fields)
        self.path_predicate = path_predicate or (lambda _path: True)

    async def __call__(self, scope, receive, send):
        """ASGI application interface."""
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        method = scope["method"]
        path = scope["path"]

        if method not in self.methods or not self.path_predicate(path):
            await self.app(scope, receive, send)
            return

        headers = dict(scope.get("headers", []))
        content_type = headers.get(b"content-type", b"").decode("latin1").lower()

        if "application/x-www-form-urlencoded" not in content_type:
            await self.app(scope, receive, send)
            return

        logger = logging.getLogger(__name__)
        logger.info(f"FormToJSON: Converting form-urlencoded to JSON for {method} {path}")

        body = b""
        while True:
            message = await receive()
            if message["type"] == "http.request":
                body += message.get("body", b"")
                if not message.get("more_body", False):
                    break

        try:
            from urllib.parse import parse_qs

            body_str = body.decode("utf-8")
            parsed = parse_qs(body_str, keep_blank_values=True)

            data = {}
            for key, values in parsed.items():
                data[key] = values[0] if len(values) == 1 else values

        except Exception as e:
            logger.error(f"FormToJSON: Failed to parse form: {e}", exc_info=True)

            async def receive_original():
                return {"type": "http.request", "body": body, "more_body": False}

            await self.app(scope, receive_original, send)
            return

        new_body = json.dumps(data, separators=(",", ":")).encode("utf-8")
        logger.info(f"FormToJSON: Converted to JSON: {new_body.decode('utf-8')}")

        new_headers = []
        for name, value in scope["headers"]:
            if name.lower() not in (b"content-type", b"content-length"):
                new_headers.append((name, value))

        new_headers.append((b"content-type", b"application/json"))
        new_headers.append((b"content-length", str(len(new_body)).encode("ascii")))
        scope["headers"] = new_headers

        async def receive_json():
            return {"type": "http.request", "body": new_body, "more_body": False}

        await self.app(scope, receive_json, send)


def setup_middlewares(
    app: FastAPI,
    *,
    enable_form_to_json: bool = False,
    form_path_prefixes: list[str] | None = None,
) -> None:
    """Set up application middleware (excluding CORS and TrustedHost).

    CORS and TrustedHost are handled separately via wrap_app() to ensure
    all responses (including exception handler responses) get proper headers.

    Args:
        app: FastAPI application
        enable_form_to_json: Enable form-to-JSON conversion middleware
        form_path_prefixes: Path prefixes to apply form conversion
    """
    if enable_form_to_json:

        def _predicate(path: str) -> bool:
            if not form_path_prefixes:
                return True
            return any(path.startswith(p) for p in form_path_prefixes)

        app.add_middleware(
            FormToJSONMiddleware,
            methods=("POST", "PUT", "PATCH"),
            merge_json_fields=("payload", "data", "user", "user_data"),
            path_predicate=_predicate,
        )

    @app.middleware("http")
    async def add_request_id(request: Request, call_next):
        """Add unique request ID to each request."""
        request_id = secrets.token_hex(8)
        request.state.request_id = request_id
        logger = logging.getLogger(__name__)

        try:
            response = await call_next(request)
            logger.info(f"Request: {request.method} {request.url.path} - Status: {response.status_code} - ID: {request_id}")
            return response
        except Exception as e:
            logger.error(f"Request: {request.method} {request.url.path} - Error: {type(e).__name__} - ID: {request_id}")
            raise


def wrap_app(
    app: FastAPI,
    cors_origins: list[str],
    cors_allow_credentials: bool,
    cors_allow_methods: list[str],
    cors_allow_headers: list[str],
    trusted_hosts: list[str],
) -> CORSMiddleware:
    """Wrap app with CORS and TrustedHost middleware.

    This wraps the entire app (including exception handlers) ensuring
    all responses get CORS headers and trusted host validation.

    Args:
        app: FastAPI application
        cors_origins: Allowed CORS origins
        cors_allow_credentials: Allow credentials in CORS
        cors_allow_methods: Allowed HTTP methods
        cors_allow_headers: Allowed HTTP headers
        trusted_hosts: Trusted host names

    Returns:
        Wrapped ASGI application
    """
    wrapped = TrustedHostMiddleware(app=app, allowed_hosts=trusted_hosts)

    return CORSMiddleware(
        app=wrapped,
        allow_origins=cors_origins,
        allow_credentials=cors_allow_credentials,
        allow_methods=cors_allow_methods,
        allow_headers=cors_allow_headers,
    )
