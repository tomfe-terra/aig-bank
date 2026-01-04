"""Application-wide constants and configuration values."""

from typing import TypedDict

APP_NAME = "AIG Bank API"
APP_VERSION = "1.0.0"

JWT_ALGORITHM = "HS256"
APP_DESCRIPTION = """
# Overview

A comprehensive banking platform providing secure financial services including account management,
credit card operations, loan processing, and payment handling.

**Core Capabilities:**
- Account creation and balance management
- Credit card issuance and payment processing
- Loan applications with approval workflows
- Inter-account money transfers
- Transaction history and reporting
- Administrative user management

**Security Features:**
- Multi-factor authentication (2FA) with OTP
- Role-based access control (USER, BANKER, ADMIN)
- Encrypted storage for sensitive data
- Account lockout protection
- Password recovery via security questions
- Comprehensive audit logging

# Registration Flow

Registration is a three-step process to ensure security:

1. **Start Registration**: Submit your username, password, and personal information (name, email, phone, address).
   You receive a temporary registration token to continue to the next step.

2. **Set Security Questions**: Using the registration token, select and answer three security questions from the
   available list. You receive an OTP secret and URI to set up two-factor authentication.

3. **Verify OTP**: Add the OTP secret to your authenticator app (Google Authenticator, Authy, etc.), generate a
   6-digit code, and submit it along with your registration token. Your account is created and activated.

After completing registration, you can log in using your username, password, and OTP code to receive an access token
and start using the banking services.

# Authentication Methods

The API supports two authentication methods to suit different use cases.

## User Authentication

For interactive user sessions such as web applications and mobile apps:

1. **Log In**: Submit your username, password, and current OTP code from your authenticator app to the login endpoint
2. **Receive Tokens**: The API returns an access token and a refresh token
3. **Make Requests**: Include the access token as a Bearer token in the `Authorization` header for all subsequent API calls
4. **Refresh Access Token**: Before your access token expires, use the refresh token along with your still-valid access
   token to obtain a new access token. This allows you to maintain continuous access without logging in again.
5. **Log Out**: When finished, call the logout endpoint to revoke your tokens

## Programmatic Authentication

For automated systems, scripts, integrations, and long-running services:

1. **Create API Key**: While authenticated, call the API key creation endpoint with a name and description
2. **Save Credentials**: Securely store the returned API key ID and secret (the secret is shown only once)
3. **Compute Signature**: For each request, generate an HMAC-SHA256 signature using a two-stage chain:
   - First digest: `HMAC-SHA256(secret, method + path)` where method is uppercase (e.g., "GET") and path is the endpoint path
   - Second digest: `HMAC-SHA256(first_digest, request_body)` where request_body is the JSON string (empty string for GET requests)
   - Encode the final digest as Base64 to get your signature
4. **Make Requests**: Include two headers in every request:
   - `Authorization: aigsignature <your_api_key_id>`
   - `Signature: <your_computed_signature>`

**Example Implementation:**

```python
def _make_request(self, method, path, body=None):
    # Capitalize method (GET, POST, etc.)
    method = method.upper()

    # Strip query parameters from path for signature (only path is signed)
    signing_path = path.split("?")[0]

    # First digest: HMAC(secret, method + path)
    digester = hmac.new(self.api_secret.encode(), None, hashlib.sha256)
    digester.update(f"{method}{signing_path}".encode())

    # Second digest: HMAC(first_digest, body)
    digester = hmac.new(digester.digest(), None, hashlib.sha256)
    if body:
        digester.update(body.encode())

    # Base64 encode the signature
    signature = base64.b64encode(digester.digest()).decode()

    # Create headers with authentication
    headers = {
        **self.headers,
        "Authorization": f"aigsignature {self.api_key_id}",
        "Signature": signature
    }

    return requests.request(method, f"{self.base_url}{path}",
                          headers=headers, data=body)
```

**Note**: API key authentication may not work correctly with `application/x-www-form-urlencoded` content.
Use `application/json` for best results.
"""
SWAGGER_URL = "/docs"
REDOC_URL = "/redoc"
OPENAPI_URL = "/openapi.json"

ENABLE_FORM_TO_JSON_MIDDLEWARE = True
FORM_TO_JSON_PATH_PREFIXES = [
    "/api/v1/users/register/start",
    "/api/v1/users/register/security-questions",
    "/api/v1/users/register/verify-otp",
    "/api/v1/users/auth/login",
    "/api/v1/users/auth/refresh",
    "/api/v1/users/auth/logout",
    "/api/v1/users/auth/me",
    "/api/v1/users/auth/password-reset/security-questions",
    "/api/v1/users/auth/password-reset/security-answers",
]

OPENAPI_TAGS = [
    {"name": "Registration", "description": "New user account registration."},
    {
        "name": "Authentication",
        "description": "User authentication, login, logout, and profile management.",
    },
    {"name": "User Profile", "description": "User profile management."},
    {"name": "API Keys", "description": "API key management for programmatic access."},
    {"name": "Transactions", "description": "Transaction history and fund transfers."},
    {"name": "Requests", "description": "View requests status."},
    {"name": "Credit Cards", "description": "Credit card management and applications."},
    {"name": "Loans", "description": "Loan applications and management."},
    {
        "name": "Savings Plans",
        "description": "Savings plans for users.",
        "externalDocs": {"description": "See Savings Plans video demonstration", "url": "https://www.youtube.com/watch?v=Y3AM00DH0Zo"},
    },
    {"name": "Banker", "description": "Banker-only operations: request decisions, moderation, and privileged actions."},
    {"name": "Admin", "description": "Admin-only operations: user management, bank monitoring, and log access."},
]

API_PREFIX = "/api/v1"

LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"


class PasswordPolicy(TypedDict):
    """Password policy requirements for user authentication."""

    min_length: int
    max_length: int
    min_uppercase: int
    min_lowercase: int
    min_digits: int
    min_special: int
    common_patterns: list[str]


PASSWORD_POLICY: PasswordPolicy = {
    "min_length": 8,
    "max_length": 128,
    "min_uppercase": 1,
    "min_lowercase": 1,
    "min_digits": 1,
    "min_special": 1,
    "common_patterns": [
        "password",
        "12345",
        "qwerty",
        "admin",
        "letmein",
        "welcome",
        "monkey",
        "dragon",
        "master",
        "sunshine",
    ],
}

BCRYPT_ROUNDS = 12

USER_ACCOUNT_POLICY = {
    "max_failed_attempts": 5,
    "lockout_duration_minutes": 30,
    "password_reset_token_expiry_hours": 24,
}

SECURITY_QUESTIONS = {
    1: "What was the name of your first pet?",
    2: "What is your mother's maiden name?",
    3: "What city were you born in?",
    4: "What is the name of your favorite teacher?",
    5: "What was the make of your first car?",
    6: "What is your favorite book?",
    7: "What was the name of your elementary school?",
    8: "What is your favorite movie?",
    9: "What street did you grow up on?",
    10: "What is your favorite food?",
    11: "What was your childhood nickname?",
    12: "What is the name of your best friend from childhood?",
    13: "What year did you graduate high school?",
    14: "What is your father's middle name?",
    15: "What was the name of your first employer?",
}

BANK_CAPITAL_ACCOUNT_NUMBER = "BANK-CAPITAL-001"
BANK_INITIAL_CAPITAL_CENTS = 1_000_000_000

SAVINGS_PLANS = [
    {
        "id": 1,
        "name": "money_market_mutual_fund",
        "display_name": "Money Market Mutual Fund",
        "description": (
            "High-yield money market account with automatic reinvestment into foreign currency accounts " "featuring compounding interest."
        ),
        "tagline": "Compounding interest on foreign currencies",
        "message": (
            "Well that's fantastic, a really smart decision, young man. We can put that deposit in a "
            "Money Market Mutual Fund, then we'll reinvest the earnings into foreign currency accounts "
            "with compounding interest aaand it's gone."
        ),
    },
    {
        "id": 2,
        "name": "treasury_bond_fund",
        "display_name": "Treasury Bond Fund",
        "description": "Government-backed treasury bonds with guaranteed returns and full FDIC insurance protection.",
        "tagline": "Government-backed security",
        "message": (
            "Excellent choice! Your funds are now secured by the full faith and credit of the " "United States Treasury aaand it's gone."
        ),
    },
    {
        "id": 3,
        "name": "high_yield_savings",
        "display_name": "High-Yield Savings Account",
        "description": (
            "Premium savings account offering competitive interest rates with instant liquidity and " "no minimum balance requirements."
        ),
        "tagline": "Premium rates, instant access",
        "message": "Congratulations on opening a High-Yield Savings Account with our most competitive rates aaand it's gone.",
    },
    {
        "id": 4,
        "name": "retirement_growth_fund",
        "display_name": "Retirement Growth Fund",
        "description": "Long-term retirement savings plan with diversified portfolio management and tax-advantaged growth potential.",
        "tagline": "Secure your retirement future",
        "message": (
            "Thank you for planning ahead! Your retirement fund is now growing with our expert " "portfolio management aaand it's gone."
        ),
    },
    {
        "id": 5,
        "name": "capital_preservation_account",
        "display_name": "Capital Preservation Account",
        "description": (
            "Conservative investment strategy focused on protecting principal while generating modest "
            "returns through low-risk instruments."
        ),
        "tagline": "Principal protection guaranteed",
        "message": "Your capital is now safely preserved in our lowest-risk investment vehicles with principal protection aaand it's gone.",
    },
]

DEFAULT_USER_ACCOUNTS = [
    {
        "username": "admin",
        "password": "Admin123!@#",
        "first_name": "Wave",
        "last_name": "Angelic",
        "email": "admin@aigbank.local",
        "role": "ADMIN",
        "otp_secret": "GNNCBSB47GMS2Y5H",
        "api_key_id": "89ec7b6f-4e16-5c99-8b81-eaa88fab611f",
        "api_secret": "jv0wJi7cgEjg5IZ_Genenh5dF-qOxdrfTf7MvKdTwSI6Rwyrqje7q3j1KkcEe-MeL52X8nYGU9I5YFVDAkabmA",
        "account_number": "1000000000000",
        "initial_balance_cents": 500000,
        "avatar_base64": (
            "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"
        ),
    },
    {
        "username": "benny",
        "password": "AndItsGone1303!",
        "first_name": "Benny",
        "last_name": "Teller",
        "email": "benny@aigbank.local",
        "role": "BANKER",
        "otp_secret": "BGPUAEHEOVSKOTV4",
        "api_key_id": "eb39a836-4084-5a4d-9d37-6bb979757899",
        "api_secret": "bK9xPm3NqR8sVw2YzA5cDf7GhJ4kLnM6oQrT1uWvX0yB8eF3gHi5jKl7mNp9qRsTuVwXyZaBcDeFgHiJkLmNo",
        "account_number": "1000000000001",
        "initial_balance_cents": 150000,
        "avatar_base64": (
            "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"
            "4GthKHfuKp5C77vvzcX76pwAAAA="
        ),
    },
    {
        "username": "pc_principal",
        "password": "StunningAndBrave1901!",
        "first_name": "Peter",
        "last_name": "Charles",
        "email": "principal@southparkelemntry.com",
        "role": "USER",
        "otp_secret": "E2U3GOTN6S2VD23Z",
        "api_key_id": "8fbdee37-b297-5721-bea0-59ca715ef204",
        "api_secret": "uS7rQp5NmK3jHg1FeDcBa9YxWv2TsR0qPnMl8KjI6hGf4EdC3bA1zYxWvUtSrQpOnMlKjIhGfEdCbAzYxWvUtS",
        "account_number": "1000000000002",
        "initial_balance_cents": 100000,
        "avatar_base64": (
            "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"
            "Q/w/9Iqu3NgAAAAA"
        ),
    },
    {
        "username": "strong_woman",
        "password": "PCBabies2307!",
        "first_name": "Strong",
        "last_name": "Woman",
        "email": "vice_principal@southparkelemntry.com",
        "role": "USER",
        "otp_secret": "KLXRRI246TZO4RCG",
        "api_key_id": "55e98972-e1e2-5c6e-9571-b6069f49020b",
        "api_secret": "aL8cE5sM2iTh9WxY3vU6tS1rQp4OnM7lK0jI9hGf8EdC6bA5zYxWvUtSrQpOnMlKjIhGfEdCbAzYxWvUtSrQp",
        "account_number": "1000000000003",
        "initial_balance_cents": 250000,
        "avatar_base64": (
            "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"
            "e99MAAAA"
        ),
    },
]
