"""Image processing utility for avatar compression and validation."""

from io import BytesIO
from typing import ClassVar

from PIL import Image

from ..core.errors import InvalidDataError


class ImageProcessor:
    """Utility for processing and validating avatar images."""

    MAX_FILE_SIZE: ClassVar[int] = 5 * 1024 * 1024

    AVATAR_SIZE: ClassVar[tuple[int, int]] = (200, 200)

    WEBP_QUALITY: ClassVar[int] = 80

    SUPPORTED_FORMATS: ClassVar[set[str]] = {"JPEG", "PNG", "GIF", "WEBP"}

    @classmethod
    def validate_image(cls, image_bytes: bytes) -> tuple[bool, str]:
        """Validate image format and size.

        Args:
            image_bytes: Raw image bytes

        Returns:
            tuple[bool, str]: (is_valid, error_message)
        """
        if len(image_bytes) > cls.MAX_FILE_SIZE:
            return False, f"Image size exceeds maximum of {cls.MAX_FILE_SIZE // (1024 * 1024)}MB"

        try:
            img = Image.open(BytesIO(image_bytes))
            img.verify()

            img = Image.open(BytesIO(image_bytes))

            if img.format not in cls.SUPPORTED_FORMATS:
                return False, f"Unsupported image format: {img.format}. Supported formats: {', '.join(cls.SUPPORTED_FORMATS)}"

            return True, ""

        except Exception as e:
            return False, f"Invalid image file: {e!s}"

    @classmethod
    def compress_avatar(cls, image_bytes: bytes) -> bytes:
        """Compress and resize image to avatar format.

        Resizes image to 200x200 and converts to WebP format with compression.

        Args:
            image_bytes: Raw image bytes

        Returns:
            bytes: Compressed WebP image bytes

        Raises:
            InvalidDataError: If image cannot be processed
        """
        try:
            img = Image.open(BytesIO(image_bytes))

            if img.mode in ("RGBA", "LA", "P"):
                background = Image.new("RGB", img.size, (255, 255, 255))
                if img.mode == "P":
                    img = img.convert("RGBA")
                background.paste(img, mask=img.split()[-1] if img.mode in ("RGBA", "LA") else None)
                img = background
            elif img.mode != "RGB":
                img = img.convert("RGB")

            img = img.resize(cls.AVATAR_SIZE, Image.Resampling.LANCZOS)

            output = BytesIO()
            img.save(output, format="WEBP", quality=cls.WEBP_QUALITY, method=6)
            output.seek(0)

            return output.read()

        except Exception as e:
            raise InvalidDataError("image", str(image_bytes[:20]), f"Failed to process image: {e!s}") from e


__all__ = ["ImageProcessor"]
