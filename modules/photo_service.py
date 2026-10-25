
from pathlib import Path
from uuid import uuid4
from io import BytesIO

from PIL import Image, UnidentifiedImageError


PROJECT_ROOT = Path(__file__).resolve().parent.parent
UPLOAD_DIR = PROJECT_ROOT / "uploads" / "complaints"

MAX_PHOTO_SIZE = 5 * 1024 * 1024

ALLOWED_FORMATS = {
    "JPEG": ".jpg",
    "PNG": ".png",
    "WEBP": ".webp",
}


def save_complaint_photo(uploaded_file):
    """Validate and securely save an uploaded complaint photo."""

    if uploaded_file is None:
        return None

    photo_bytes = uploaded_file.getvalue()

    if not photo_bytes:
        raise ValueError("The uploaded photo is empty.")

    if len(photo_bytes) > MAX_PHOTO_SIZE:
        raise ValueError("The photo must be 5 MB or smaller.")

    try:
        with Image.open(BytesIO(photo_bytes)) as image:
            detected_format = image.format

            if detected_format not in ALLOWED_FORMATS:
                raise ValueError(
                    "Only JPEG, PNG and WebP photos are allowed."
                )

            image.verify()

    except (UnidentifiedImageError, OSError):
        raise ValueError(
            "The uploaded file is not a valid image."
        )

    extension = ALLOWED_FORMATS[detected_format]
    filename = f"{uuid4().hex}{extension}"

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    photo_path = UPLOAD_DIR / filename

    # Re-encode the image to avoid storing its original
    # metadata or other non-image contents.
    try:
        with Image.open(BytesIO(photo_bytes)) as image:
            if detected_format == "JPEG":
                clean_image = image.convert("RGB")
            elif image.mode in ("RGBA", "LA"):
                clean_image = image.convert("RGBA")
            else:
                clean_image = image.convert("RGB")

            clean_image.save(
                photo_path,
                format=detected_format,
            )

    except Exception:
        photo_path.unlink(missing_ok=True)
        raise ValueError("Unable to process the uploaded photo.")

    # Store a relative path in SQLite.
    return f"uploads/complaints/{filename}"
