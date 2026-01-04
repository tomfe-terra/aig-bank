"""FastAPI application factory and configuration."""

from fastapi import FastAPI

from .config import settings
from .constants import (
    API_PREFIX,
    APP_DESCRIPTION,
    APP_NAME,
    APP_VERSION,
    ENABLE_FORM_TO_JSON_MIDDLEWARE,
    FORM_TO_JSON_PATH_PREFIXES,
    OPENAPI_TAGS,
    OPENAPI_URL,
    REDOC_URL,
    SWAGGER_URL,
)
from .errors import global_exception_handler
from .lifespan import lifespan
from .logging import setup_logging
from .middleware import setup_middlewares, wrap_app
from .openapi import customize_openapi_schema
from .routers import setup_routers


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    setup_logging(settings.log_level)

    app = FastAPI(
        title=APP_NAME,
        version=APP_VERSION,
        description=APP_DESCRIPTION,
        lifespan=lifespan,
        debug=settings.debug,
        docs_url=SWAGGER_URL,
        redoc_url=REDOC_URL,
        openapi_url=OPENAPI_URL,
        openapi_tags=OPENAPI_TAGS,
    )

    setup_routers(app, API_PREFIX)

    setup_middlewares(
        app,
        enable_form_to_json=ENABLE_FORM_TO_JSON_MIDDLEWARE,
        form_path_prefixes=FORM_TO_JSON_PATH_PREFIXES,
    )

    customize_openapi_schema(
        app,
        enable_form_to_json=ENABLE_FORM_TO_JSON_MIDDLEWARE,
        form_path_prefixes=FORM_TO_JSON_PATH_PREFIXES,
        docs_verbosity=settings.docs_verbosity,
    )

    app.add_exception_handler(Exception, global_exception_handler)

    return wrap_app(
        app,
        cors_origins=settings.cors_origins,
        cors_allow_credentials=settings.cors_allow_credentials,
        cors_allow_methods=settings.cors_allow_methods,
        cors_allow_headers=settings.cors_allow_headers,
        trusted_hosts=settings.trusted_hosts,
    )
