
from pathlib import Path
from io import BytesIO
import sys

from PIL import Image

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from database.init_db import get_connection
from modules.photo_service import save_complaint_photo
from modules.report_service import submit_report, get_report_by_id


class FakeUploadedFile:
    def __init__(self, content):
        self.content = content

    def getvalue(self):
        return self.content


report_id = None
saved_photo = None

try:
    # Create a sample image for testing.
    buffer = BytesIO()
    Image.new(
        "RGB",
        (100, 100),
        color="blue"
    ).save(buffer, format="PNG")

    # Save the test image.
    photo_path = save_complaint_photo(
        FakeUploadedFile(buffer.getvalue())
    )

    saved_photo = PROJECT_ROOT / photo_path

    print("PASS: Test photo saved.")

    # Submit a complaint with the saved photo.
    report_id = submit_report(
        title="TEST - Photo attachment",
        category="Roads & public property",
        description="Testing a complaint with a photo.",
        ward_id=12,
        locality="Test locality",
        location_details="Near the main road",
        photo_path=photo_path,
    )

    print("Test report created:", report_id)

    # Retrieve the complaint from SQLite.
    report = get_report_by_id(report_id)

    assert report is not None
    assert report["photo_path"] == photo_path
    assert saved_photo.is_file()

    print("PASS: SQLite stored the correct photo path.")
    print("PASS: The attached photo exists.")
    print("All report photo attachment tests passed!")

finally:
    # Remove only the temporary test report.
    if report_id is not None:
        with get_connection() as connection:
            connection.execute(
                "DELETE FROM civic_reports WHERE report_id = ?",
                (report_id,)
            )

        print("Temporary test report removed.")

    # Remove only the temporary test photo.
    if saved_photo is not None:
        saved_photo.unlink(missing_ok=True)
        print("Temporary test photo removed.")
