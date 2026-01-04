"""User profile management endpoints."""

from fastapi import APIRouter, Depends, File, UploadFile, status
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from ...api.deps import get_current_user
from ...core.db import get_db
from ...core.errors import ErrorCode
from ...schemas.user_schemas import AvatarUploadResult, ProfileUpdate, ProfileUpdateResult
from ...services.user_service import UserService

router = APIRouter(prefix="/users/profile", tags=["User Profile"])


@router.patch(
    "",
    response_model=ProfileUpdateResult,
    status_code=status.HTTP_200_OK,
    summary="Update User Profile",
    description="""Update the current user's profile information.

Only provided fields will be updated (partial update supported).
All fields are optional.""",
    responses={
        status.HTTP_200_OK: {
            "model": ProfileUpdateResult,
            "description": "Profile updated successfully",
            "content": {
                "application/json": {
                    "examples": {
                        "profile_updated": {
                            "summary": "Profile updated",
                            "value": {
                                "message": "Profile updated successfully",
                                "user": {
                                    "id": "550e8400-e29b-41d4-a716-446655440000",
                                    "username": "johndoe",
                                    "email": "john.updated@example.com",
                                    "phone": "+1234567890",
                                    "address": "456 New St, City, Country",
                                    "first_name": "John",
                                    "last_name": "Doe",
                                    "role": "USER",
                                    "status": "ENABLED",
                                    "has_avatar": False,
                                },
                            },
                        },
                    },
                },
            },
        },
        status.HTTP_400_BAD_REQUEST: {
            "description": "Bad request",
            "content": {
                "application/json": {
                    "examples": {
                        "validation_error": {
                            "summary": "Validation error",
                            "value": {
                                "error": ErrorCode.VALIDATION_ERROR.value,
                                "details": "email: Invalid email format",
                                "request_id": "938304120f4492de",
                            },
                        },
                        "invalid_data": {
                            "summary": "No fields provided",
                            "value": {
                                "error": ErrorCode.INVALID_DATA.value,
                                "details": "No fields provided to update",
                                "request_id": "938304120f4492de",
                            },
                        },
                    },
                },
            },
        },
        status.HTTP_401_UNAUTHORIZED: {
            "description": "Unauthorized",
            "content": {
                "application/json": {
                    "examples": {
                        "authentication_required": {
                            "summary": "Authentication required",
                            "value": {
                                "error": ErrorCode.AUTHENTICATION_REQUIRED.value,
                                "details": "Authentication is required to access this resource",
                                "request_id": "938304120f4492de",
                            },
                        },
                    },
                },
            },
        },
    },
)
async def update_profile(
    update_data: ProfileUpdate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ProfileUpdateResult:
    """Update user profile.

    Args:
        update_data: Profile update data
        current_user: Authenticated user context
        db: Database session

    Returns:
        ProfileUpdateResult: Success message with updated user
    """
    user_service = UserService(db)
    user_id = current_user["user_id"]
    return await user_service.update_profile(user_id, update_data)


@router.post(
    "/avatar",
    response_model=AvatarUploadResult,
    status_code=status.HTTP_200_OK,
    summary="Upload User Avatar",
    description="""Upload or update the current user's avatar image.

The image will be automatically resized to 200x200 pixels and compressed to WebP format.

Supported formats: JPEG, PNG, GIF, WebP
Maximum file size: 5MB (before compression)""",
    responses={
        status.HTTP_200_OK: {
            "model": AvatarUploadResult,
            "description": "Avatar uploaded successfully",
            "content": {
                "application/json": {
                    "examples": {
                        "avatar_uploaded": {
                            "summary": "Avatar uploaded",
                            "value": {
                                "message": "Avatar uploaded successfully",
                                "has_avatar": True,
                            },
                        },
                    },
                },
            },
        },
        status.HTTP_400_BAD_REQUEST: {
            "description": "Bad request",
            "content": {
                "application/json": {
                    "examples": {
                        "invalid_data": {
                            "summary": "Invalid image",
                            "value": {
                                "error": ErrorCode.INVALID_DATA.value,
                                "details": "Unsupported image format: BMP. Supported formats: JPEG, PNG, GIF, WEBP",
                                "request_id": "938304120f4492de",
                            },
                        },
                    },
                },
            },
        },
        status.HTTP_401_UNAUTHORIZED: {
            "description": "Unauthorized",
            "content": {
                "application/json": {
                    "examples": {
                        "authentication_required": {
                            "summary": "Authentication required",
                            "value": {
                                "error": ErrorCode.AUTHENTICATION_REQUIRED.value,
                                "details": "Authentication is required to access this resource",
                                "request_id": "938304120f4492de",
                            },
                        },
                    },
                },
            },
        },
    },
)
async def upload_avatar(
    file: UploadFile = File(..., description="Avatar image file"),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AvatarUploadResult:
    """Upload user avatar.

    Args:
        file: Uploaded image file
        current_user: Authenticated user context
        db: Database session

    Returns:
        AvatarUploadResult: Success message
    """
    user_service = UserService(db)
    user_id = current_user["user_id"]
    return await user_service.upload_avatar(user_id, file)


@router.get(
    "/avatar",
    status_code=status.HTTP_200_OK,
    summary="Get My Avatar",
    description="""Get the current user's avatar image.

Returns the avatar as a WebP image. Requires authentication.

The response includes cache headers for optimal performance.""",
    responses={
        status.HTTP_200_OK: {
            "description": "Avatar image",
            "content": {
                "image/webp": {
                    "example": "<binary image data>",
                },
            },
        },
        status.HTTP_400_BAD_REQUEST: {
            "description": "No avatar",
            "content": {
                "application/json": {
                    "examples": {
                        "no_avatar": {
                            "summary": "User has no avatar",
                            "value": {
                                "error": ErrorCode.RESOURCE_NOT_FOUND.value,
                                "details": "User 550e8400-e29b-41d4-a716-446655440000 has no avatar",
                                "request_id": "938304120f4492de",
                            },
                        },
                    },
                },
            },
        },
        status.HTTP_401_UNAUTHORIZED: {
            "description": "Unauthorized",
            "content": {
                "application/json": {
                    "examples": {
                        "authentication_required": {
                            "summary": "Authentication required",
                            "value": {
                                "error": ErrorCode.AUTHENTICATION_REQUIRED.value,
                                "details": "Authentication is required to access this resource",
                                "request_id": "938304120f4492de",
                            },
                        },
                    },
                },
            },
        },
    },
)
async def get_avatar(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Response:
    """Get current user's avatar.

    Args:
        current_user: Authenticated user context
        db: Database session

    Returns:
        Response: Avatar image with WebP content-type
    """
    user_service = UserService(db)
    user_id = current_user["user_id"]
    avatar_bytes = await user_service.get_avatar(user_id)

    return Response(
        content=avatar_bytes,
        media_type="image/webp",
        headers={
            "Cache-Control": "private, max-age=3600",
            "Content-Disposition": f'inline; filename="avatar-{user_id}.webp"',
        },
    )


@router.delete(
    "/avatar",
    status_code=status.HTTP_200_OK,
    summary="Delete User Avatar",
    description="""Delete the current user's avatar image.""",
    responses={
        status.HTTP_200_OK: {
            "description": "Avatar deleted successfully",
            "content": {
                "application/json": {
                    "examples": {
                        "avatar_deleted": {
                            "summary": "Avatar deleted",
                            "value": {
                                "message": "Avatar deleted successfully",
                            },
                        },
                    },
                },
            },
        },
        status.HTTP_401_UNAUTHORIZED: {
            "description": "Unauthorized",
            "content": {
                "application/json": {
                    "examples": {
                        "authentication_required": {
                            "summary": "Authentication required",
                            "value": {
                                "error": ErrorCode.AUTHENTICATION_REQUIRED.value,
                                "details": "Authentication is required to access this resource",
                                "request_id": "938304120f4492de",
                            },
                        },
                    },
                },
            },
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "User not found",
            "content": {
                "application/json": {
                    "examples": {
                        "user_not_found": {
                            "summary": "User not found",
                            "value": {
                                "error": ErrorCode.RESOURCE_NOT_FOUND.value,
                                "details": "User not found",
                                "request_id": "938304120f4492de",
                            },
                        },
                    },
                },
            },
        },
    },
)
async def delete_avatar(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Delete user avatar.

    Args:
        current_user: Authenticated user context
        db: Database session

    Returns:
        dict: Success message
    """
    user_service = UserService(db)
    user_id = current_user["user_id"]
    return await user_service.delete_avatar(user_id)
