"""User registration endpoints (no authentication required)."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.constants import SECURITY_QUESTIONS
from ...core.db import get_db
from ...core.errors import ErrorCode
from ...schemas.registration_schemas import (
    OTPSetup,
    RegistrationComplete,
    RegistrationToken,
    SecurityQuestionOption,
    SecurityQuestionsList,
    SetSecurityQuestions,
    StartRegistration,
    VerifyOTP,
)
from ...services.user_service import UserService

router = APIRouter(prefix="/users", tags=["Registration"])


@router.post(
    "/register/start",
    response_model=RegistrationToken,
    status_code=status.HTTP_200_OK,
    summary="Start Registration",
    description="Start the registration process with basic information.",
    responses={
        status.HTTP_200_OK: {
            "model": RegistrationToken,
            "description": "Success",
            "content": {
                "application/json": {
                    "examples": {
                        "registration_started": {
                            "summary": "Registration started",
                            "value": {
                                "message": "Registration started successfully.",
                                "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VybmFtZSI6ImpvaG5kb2UiLCJzdGVwIjoxfQ.abc123",
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
                        "username_exists": {
                            "summary": "Username already taken",
                            "value": {
                                "error": ErrorCode.ALREADY_EXISTS.value,
                                "details": "Username already exists",
                                "request_id": "938304120f4492de",
                            },
                        },
                        "weak_password": {
                            "summary": "Password too weak",
                            "value": {
                                "error": ErrorCode.PASSWORD_POLICY_ERROR.value,
                                "details": "Password must be at least 8 characters long",
                                "request_id": "938304120f4492de",
                            },
                        },
                        "validation_error": {
                            "summary": "Request validation failed",
                            "value": {
                                "error": ErrorCode.VALIDATION_ERROR.value,
                                "details": "Name must be 1-255 characters, letters, spaces, hyphens and apostrophes only",
                                "request_id": "938304120f4492de",
                            },
                        },
                    },
                },
            },
        },
    },
)
async def start_registration(
    request: StartRegistration,
    db: AsyncSession = Depends(get_db),
) -> RegistrationToken:
    """Start registration process - validates data but does not create user.

    Args:
        request: Basic registration data
        db: Database session

    Returns:
        RegistrationToken: Encrypted token for next step
    """
    user_service = UserService(db)
    return await user_service.start_registration(request)


@router.post(
    "/register/security-questions",
    response_model=OTPSetup,
    status_code=status.HTTP_200_OK,
    summary="Set Security Questions",
    description="""Set 3 security questions for account recovery.""",
    responses={
        status.HTTP_200_OK: {
            "model": OTPSetup,
            "description": "Success",
            "content": {
                "application/json": {
                    "examples": {
                        "otp_setup": {
                            "summary": "Security questions set - OTP setup required",
                            "value": {
                                "message": "Security questions set successfully.",
                                "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VybmFtZSI6ImpvaG5kb2UiLCJzdGVwIjoxfQ.abc123",
                                "otp_uri": "otpauth://totp/BankApp:johndoe?secret=JBSWY3DPEHPK3PXP&issuer=BankApp",
                                "otp_secret": "JBSWY3DPEHPK3PXP",
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
                            "summary": "Input validation failed",
                            "value": {
                                "error": ErrorCode.VALIDATION_ERROR.value,
                                "details": "Invalid security question ID: 999",
                                "request_id": "938304120f4492de",
                            },
                        },
                        "invalid_token": {
                            "summary": "Corrupted token data",
                            "value": {
                                "error": ErrorCode.INVALID_TOKEN.value,
                                "details": "Token data is corrupted or invalid",
                                "request_id": "938304120f4492de",
                            },
                        },
                        "invalid_padding": {
                            "summary": "Invalid padding",
                            "value": {
                                "error": ErrorCode.INVALID_PADDING.value,
                                "details": "Invalid padding in encrypted data",
                                "request_id": "938304120f4492de",
                            },
                        },
                    },
                },
            },
        },
    },
)
async def set_security_questions(
    request: SetSecurityQuestions,
    db: AsyncSession = Depends(get_db),
) -> OTPSetup:
    """Set security questions - validates but does not create user.

    Args:
        request: Security questions with registration token
        db: Database session

    Returns:
        OTPSetup: OTP setup information and updated token
    """
    user_service = UserService(db)
    return await user_service.set_security_questions(request)


@router.post(
    "/register/verify-otp",
    response_model=RegistrationComplete,
    status_code=status.HTTP_201_CREATED,
    summary="Verify OTP and Create Account",
    description="""Verify your OTP code to complete registration and create your account.

The OTP secret is permanently stored and will be required for future logins.""",
    responses={
        status.HTTP_201_CREATED: {
            "model": RegistrationComplete,
            "description": "Success",
            "content": {
                "application/json": {
                    "examples": {
                        "account_created": {
                            "summary": "Account created successfully",
                            "value": {
                                "message": "Registration completed successfully! Your account is now active.",
                                "id": "550e8400-e29b-41d4-a716-446655440000",
                                "username": "johndoe",
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
                        "invalid_token": {
                            "summary": "Corrupted token data",
                            "value": {
                                "error": ErrorCode.INVALID_TOKEN.value,
                                "details": "Token data is corrupted or invalid",
                                "request_id": "938304120f4492de",
                            },
                        },
                        "username_taken": {
                            "summary": "Username taken during registration",
                            "value": {
                                "error": ErrorCode.ALREADY_EXISTS.value,
                                "details": "Username already exists",
                                "request_id": "938304120f4492de",
                            },
                        },
                        "validation_error": {
                            "summary": "Input validation failed",
                            "value": {
                                "error": ErrorCode.VALIDATION_ERROR.value,
                                "details": "OTP code must be exactly 6 digits",
                                "request_id": "938304120f4492de",
                            },
                        },
                        "invalid_otp": {
                            "summary": "Invalid OTP code",
                            "value": {
                                "error": ErrorCode.INVALID_OTP.value,
                                "details": "Invalid OTP code",
                                "request_id": "938304120f4492de",
                            },
                        },
                    },
                },
            },
        },
    },
)
async def verify_otp_and_complete(
    request: VerifyOTP,
    db: AsyncSession = Depends(get_db),
) -> RegistrationComplete:
    """Verify OTP and create user account.

    Args:
        request: Registration token and OTP code
        db: Database session

    Returns:
        RegistrationComplete: Success message with created user info
    """
    user_service = UserService(db)
    return await user_service.verify_otp_and_complete_registration(request)


@router.get(
    "/register/security-questions",
    response_model=SecurityQuestionsList,
    status_code=status.HTTP_200_OK,
    summary="Get Available Security Questions",
    description="""Get the list of available security questions.

Use these question IDs when registering a new account.
You must select 3 different questions from this list.""",
    responses={
        status.HTTP_200_OK: {
            "model": SecurityQuestionsList,
            "description": "List of available security questions",
            "content": {
                "application/json": {
                    "examples": {
                        "questions_list": {
                            "summary": "Available security questions",
                            "value": {
                                "questions": [
                                    {"id": 1, "question": "What was the name of your first pet?"},
                                    {"id": 2, "question": "In what city were you born?"},
                                    {"id": 3, "question": "What is your mother's maiden name?"},
                                ],
                            },
                        },
                    },
                },
            },
        },
    },
)
async def get_security_questions() -> SecurityQuestionsList:
    """Get list of available security questions.

    Returns:
        SecurityQuestionsList: List of question IDs and texts
    """
    questions = [SecurityQuestionOption(id=qid, question=question) for qid, question in SECURITY_QUESTIONS.items()]
    return SecurityQuestionsList(questions=questions)
