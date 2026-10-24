
from pathlib import Path
from io import BytesIO
import sys

from PIL import Image

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from modules.photo_service import (
    save_complaint_photo,
    MAX_PHOTO_SIZE,
)


class FakeUploadedFile:
    """Simulate a file uploaded through Streamlit."""

    def __init__(self, content):
        self.content = content

    def getvalue(self):
        return self.content


saved_files = []

try:
    # Test 1: Save a valid PNG image.
    image_buffer = BytesIO()

    Image.new(
        "RGB",
        (100, 100),
        color="blue",
    ).save(image_buffer, format="PNG")

    uploaded_file = FakeUploadedFile(
        image_buffer.getvalue()
    )

    photo_path = save_complaint_photo(uploaded_file)
    saved_files.append(PROJECT_ROOT / photo_path)

    assert (PROJECT_ROOT / photo_path).exists()

    print("PASS: Valid PNG photo saved successfully.")

    # Test 2: Reject an empty file.
    try:
        save_complaint_photo(FakeUploadedFile(b""))
        raise AssertionError("Empty file was accepted!")
    except ValueError:
        print("PASS: Empty file rejected.")

    # Test 3: Reject a non-image file.
    try:
        save_complaint_photo(
            FakeUploadedFile(b"This is not an image.")
        )
        raise AssertionError("Invalid image was accepted!")
    except ValueError:
        print("PASS: Invalid image rejected.")

    # Test 4: Reject oversized files.
    oversized_file = FakeUploadedFile(
        b"x" * (MAX_PHOTO_SIZE + 1)
    )

    try:
        save_complaint_photo(oversized_file)
        raise AssertionError("Oversized photo was accepted!")
    except ValueError:
        print("PASS: Oversized photo rejected.")

    # Test 5: No photo is optional.
    assert save_complaint_photo(None) is None

    print("PASS: Optional photo handled correctly.")

    print("All photo service tests passed!")

finally:
    # Remove files created during testing.
    for file_path in saved_files:
        file_path.unlink(missing_ok=True)

    print("Temporary test photos removed.")
