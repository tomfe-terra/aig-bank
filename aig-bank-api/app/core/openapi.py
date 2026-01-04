"""OpenAPI schema customization and manipulation."""

from fastapi import FastAPI

from .enums import DocsVerbosity


def strip_openapi_by_verbosity(schema: dict, verbosity: DocsVerbosity) -> dict:
    """Strip OpenAPI schema based on verbosity level.

    Args:
        schema: The OpenAPI schema dictionary
        verbosity: The verbosity level

    Returns:
        Modified schema dictionary
    """

    def strip_examples(obj: dict | list | None) -> None:
        """Recursively remove examples from schema objects."""
        if isinstance(obj, dict):
            obj.pop("example", None)
            obj.pop("examples", None)
            for value in obj.values():
                strip_examples(value)
        elif isinstance(obj, list):
            for item in obj:
                strip_examples(item)

    def strip_descriptions(obj: dict | list | None) -> None:
        """Recursively remove descriptions from schema objects."""
        if isinstance(obj, dict):
            obj.pop("description", None)
            for value in obj.values():
                strip_descriptions(value)
        elif isinstance(obj, list):
            for item in obj:
                strip_descriptions(item)

    def strip_non_success_responses(operation: dict) -> None:
        """Remove non-2xx response statuses from an operation."""
        if "responses" not in operation:
            return
        responses = operation["responses"]
        keys_to_remove = [key for key in responses if key != "default" and not key.startswith("2")]
        for key in keys_to_remove:
            responses.pop(key, None)

    def strip_operation_metadata(operation: dict) -> None:
        """Remove summary, tags, and security from an operation."""
        operation.pop("summary", None)
        operation.pop("tags", None)
        operation.pop("security", None)

    def strip_422_responses(schema: dict) -> None:
        """Remove 422 validation error responses from all operations."""
        paths = schema.get("paths", {})
        for path_item in paths.values():
            if isinstance(path_item, dict):
                for operation in path_item.values():
                    if isinstance(operation, dict) and "responses" in operation:
                        operation["responses"].pop("422", None)

    def strip_validation_error_schemas(schema: dict) -> None:
        """Remove ValidationError and HTTPValidationError schemas from components."""
        components = schema.get("components", {})
        if components and "schemas" in components:
            components["schemas"].pop("ValidationError", None)
            components["schemas"].pop("HTTPValidationError", None)

    strip_422_responses(schema)
    strip_validation_error_schemas(schema)

    if verbosity == DocsVerbosity.FULL:
        return schema

    if verbosity in (DocsVerbosity.MEDIUM, DocsVerbosity.MINIMAL):
        strip_examples(schema)

    if verbosity == DocsVerbosity.MINIMAL:
        strip_descriptions(schema)

        paths = schema.get("paths", {})
        for path_item in paths.values():
            if isinstance(path_item, dict):
                for operation in path_item.values():
                    if isinstance(operation, dict):
                        strip_non_success_responses(operation)
                        strip_operation_metadata(operation)

        components = schema.get("components", {})
        if components:
            components.pop("securitySchemes", None)

        schema.pop("tags", None)

    return schema


def add_form_content_types_to_openapi(
    app: FastAPI,
    form_path_prefixes: list[str] | None = None,
    docs_verbosity: DocsVerbosity = DocsVerbosity.FULL,
) -> None:
    """Patch OpenAPI to advertise form content types for matching paths.

    For operations matching form_path_prefixes that have application/json in requestBody,
    also advertise application/x-www-form-urlencoded with the same schema.

    This resolves $ref references to their actual schema definitions so Swagger UI
    can properly render form fields.

    Args:
        app: FastAPI application
        form_path_prefixes: List of path prefixes to patch. If None or empty, patches all paths.
        docs_verbosity: Documentation verbosity level to apply
    """
    original_openapi = app.openapi

    def resolve_refs(schema_obj: dict, components: dict) -> dict:
        """Recursively resolve $ref references in a schema object.

        Returns a fully resolved schema without any $ref pointers.
        """
        if not isinstance(schema_obj, dict):
            return schema_obj

        if "$ref" in schema_obj:
            ref_path = schema_obj["$ref"]
            if ref_path.startswith("#/components/schemas/"):
                schema_name = ref_path.split("/")[-1]
                resolved = components.get("schemas", {}).get(schema_name, {})
                return resolve_refs(resolved.copy(), components)
            return schema_obj

        result = {}
        for key, value in schema_obj.items():
            if isinstance(value, dict):
                result[key] = resolve_refs(value, components)
            elif isinstance(value, list):
                result[key] = [resolve_refs(item, components) if isinstance(item, dict) else item for item in value]
            else:
                result[key] = value

        return result

    def should_patch_path(path: str) -> bool:
        """Check if the path should be patched based on prefixes."""
        if not form_path_prefixes:
            return True
        return any(path.startswith(prefix) for prefix in form_path_prefixes)

    def custom_openapi():
        if app.openapi_schema:
            return app.openapi_schema

        schema = original_openapi()

        components = schema.get("components", {})
        paths = schema.get("paths") or {}

        for _path, methods in paths.items():
            if not should_patch_path(_path):
                continue

            if not isinstance(methods, dict):
                continue
            for operation in methods.values():
                if not isinstance(operation, dict):
                    continue
                rb = operation.get("requestBody")
                if not (rb and isinstance(rb, dict)):
                    continue
                content = rb.get("content") or {}
                json_ct = content.get("application/json")
                if not json_ct:
                    continue
                json_schema = json_ct.get("schema")
                if not json_schema:
                    continue

                resolved_schema = resolve_refs(json_schema, components)

                if "application/x-www-form-urlencoded" not in content:
                    content["application/x-www-form-urlencoded"] = {"schema": resolved_schema}

                rb["content"] = content

        schema = strip_openapi_by_verbosity(schema, docs_verbosity)

        app.openapi_schema = schema
        return app.openapi_schema

    app.openapi = custom_openapi


def customize_openapi_schema(
    app: FastAPI,
    *,
    enable_form_to_json: bool = False,
    form_path_prefixes: list[str] | None = None,
    docs_verbosity: DocsVerbosity = DocsVerbosity.FULL,
) -> None:
    """Customize the OpenAPI schema for the application.

    Args:
        app: FastAPI application
        enable_form_to_json: Whether to add form content types to the schema
        form_path_prefixes: Path prefixes to apply form content types to
        docs_verbosity: Documentation verbosity level
    """
    if enable_form_to_json:
        add_form_content_types_to_openapi(app, form_path_prefixes=form_path_prefixes, docs_verbosity=docs_verbosity)
    else:
        if docs_verbosity != DocsVerbosity.FULL:
            add_form_content_types_to_openapi(app, form_path_prefixes=None, docs_verbosity=docs_verbosity)


__all__ = [
    "add_form_content_types_to_openapi",
    "customize_openapi_schema",
    "strip_openapi_by_verbosity",
]
