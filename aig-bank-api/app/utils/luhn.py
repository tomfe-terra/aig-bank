"""Luhn algorithm implementation for credit card validation."""

from datetime import UTC


def validate_luhn(card_number: str) -> bool:
    """Validate a credit card number using the Luhn algorithm.

    Args:
        card_number: The card number as a string (digits only)

    Returns:
        bool: True if the card number is valid according to Luhn algorithm

    Raises:
        ValueError: If the card number contains non-digit characters
    """
    card_number = card_number.replace(" ", "").replace("-", "")

    if not card_number.isdigit():
        return False

    if len(card_number) != 16:
        return False

    digits = [int(digit) for digit in reversed(card_number)]

    for i in range(1, len(digits), 2):
        digits[i] *= 2
        if digits[i] > 9:
            digits[i] -= 9

    total = sum(digits)

    return total % 10 == 0


def calculate_luhn_checksum(card_number: str) -> int:
    """Calculate the Luhn checksum digit for a card number.

    Args:
        card_number: The card number as a string (digits only, without check digit)

    Returns:
        int: The checksum digit (0-9)
    """
    card_number = card_number.replace(" ", "").replace("-", "")

    if not card_number.isdigit():
        raise ValueError("Card number must contain only digits")

    if len(card_number) != 15:
        raise ValueError("Card number must be exactly 15 digits (before check digit)")

    test_card = card_number + "0"
    digits = [int(digit) for digit in reversed(test_card)]

    for i in range(1, len(digits), 2):
        digits[i] *= 2
        if digits[i] > 9:
            digits[i] -= 9

    total = sum(digits)

    remainder = total % 10
    if remainder == 0:
        return 0
    else:
        return 10 - remainder


def validate_expiry_date(exp_month: int, exp_year: int) -> bool:
    """Validate expiry date is in the future.

    Args:
        exp_month: Month (1-12)
        exp_year: Year (4 digits)

    Returns:
        bool: True if expiry date is valid and in the future
    """
    if not (1 <= exp_month <= 12):
        return False

    from datetime import datetime

    current_year = datetime.now(UTC).year
    current_month = datetime.now(UTC).month

    return not (exp_year < current_year or (exp_year == current_year and exp_month < current_month))


def generate_card_number(card_brand: str, length: int | None = None) -> str:
    """Generate a valid 16-digit card number for a given brand using Luhn algorithm.

    Args:
        card_brand: Card brand (VISA, MASTERCARD, AMERICAN_EXPRESS, DISCOVER)
        length: Optional length validation (must be 16 for this simulation)

    Returns:
        str: A valid 16-digit card number for the specified brand

    Raises:
        ValueError: If card_brand is not supported or length is not 16
    """
    import random

    brand_configs: dict[str, dict[str, list[str]]] = {
        "VISA": {
            "prefixes": ["4"],
        },
        "MASTERCARD": {
            "prefixes": [
                "51",
                "52",
                "53",
                "54",
                "55",
                "2221",
            ],
        },
        "AMERICAN_EXPRESS": {
            "prefixes": [
                "34",
                "37",
            ],
        },
        "DISCOVER": {
            "prefixes": [
                "6011",
                "622126",
                "622127",
                "622128",
                "622129",
                "62213",
                "62214",
                "62215",
                "62216",
                "62217",
                "62218",
                "62219",
                "6222",
                "6223",
                "6224",
                "6225",
                "6226",
                "6227",
                "6228",
                "6229",
                "644",
                "645",
                "646",
                "647",
                "648",
                "649",
                "65",
            ],
        },
    }

    if card_brand not in brand_configs:
        raise ValueError(f"Unsupported card brand: {card_brand}. " f"Supported brands: VISA, MASTERCARD, AMERICAN_EXPRESS, DISCOVER")

    config = brand_configs[card_brand]

    if length is not None and length != 16:
        raise ValueError("All PANs must be exactly 16 digits")
    length = 16

    prefix: str = random.choice(config["prefixes"])

    remaining_length = length - len(prefix) - 1

    body_digits = "".join(str(random.randint(0, 9)) for _ in range(remaining_length))

    card_without_check = prefix + body_digits

    check_digit = calculate_luhn_checksum(card_without_check)

    return card_without_check + str(check_digit)


def generate_cvv(card_brand: str) -> str:
    """Generate a CVV for a card.

    Args:
        card_brand: Card brand (VISA, MASTERCARD, DISCOVER)

    Returns:
        str: A valid 3-digit CVV
    """
    import random

    return str(random.randint(100, 999))


def generate_expiry_date(years_ahead: int = 3) -> tuple[int, int]:
    """Generate a future expiry date for a card.

    Args:
        years_ahead: Number of years in the future (default: 3)

    Returns:
        tuple[int, int]: (month, year) for expiry
    """
    from datetime import datetime
    import random

    current_year = datetime.now(UTC).year
    current_month = datetime.now(UTC).month

    exp_year = current_year + random.randint(1, years_ahead)

    exp_month = random.randint(1, 12)

    if exp_year == current_year and exp_month <= current_month:
        exp_month = current_month + 1
        if exp_month > 12:
            exp_month = 1
            exp_year += 1

    return exp_month, exp_year
