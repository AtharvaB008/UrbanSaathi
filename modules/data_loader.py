
from pathlib import Path

import geopandas as gpd
import numpy as np
import rasterio
from rasterio.mask import mask


PROJECT_ROOT = Path(__file__).resolve().parent.parent

WARD_FILE = PROJECT_ROOT / "data" / "mangaluru_wards.geojson"
POPULATION_FILE = (
    PROJECT_ROOT / "data" / "mangaluru_population_density.tif"
)

# The raster contains extreme negative sentinel values.
# Keep only finite, non-negative pixels.
INVALID_RASTER_THRESHOLD = -1e20


def load_wards():
    """Load and validate Mangaluru ward boundaries."""
    if not WARD_FILE.exists():
        raise FileNotFoundError(f"Ward file not found: {WARD_FILE}")

    wards = gpd.read_file(WARD_FILE)

    if wards.empty:
        raise ValueError("The ward dataset is empty.")

    if wards.crs is None:
        raise ValueError("Ward boundaries have no CRS.")

    wards = wards.to_crs("EPSG:4326")

    if wards.geometry.isna().any() or wards.geometry.is_empty.any():
        raise ValueError("Ward boundaries contain empty geometries.")

    if not wards.geometry.is_valid.all():
        raise ValueError("Ward boundaries contain invalid geometries.")

    if "KGISWardID" not in wards.columns:
        raise ValueError("Missing KGISWardID ward identifier.")

    return wards


def load_population_raster():
    """Read population raster data and mask invalid pixels."""
    if not POPULATION_FILE.exists():
        raise FileNotFoundError(
            f"Population raster not found: {POPULATION_FILE}"
        )

    with rasterio.open(POPULATION_FILE) as src:
        data = src.read(1, masked=True).astype("float32")
        values = data.filled(np.nan)

        valid_mask = (
            np.isfinite(values)
            & (values >= 0)
            & (values > INVALID_RASTER_THRESHOLD)
        )

        cleaned = np.where(valid_mask, values, np.nan)

        return {
            "data": cleaned,
            "valid_mask": valid_mask,
            "transform": src.transform,
            "crs": src.crs,
            "bounds": src.bounds,
            "nodata": src.nodata,
        }


def get_ward_population_summary(ward):
    """Return descriptive raster statistics for a ward.

    Values are not assigned units or a reference year here:
    those still need verification against the source service.
    """
    raster = load_population_raster()

    if ward.crs is None:
        raise ValueError("The selected ward has no CRS.")

    ward_geometry = ward.to_crs(raster["crs"]).geometry.iloc[0]

    with rasterio.open(POPULATION_FILE) as src:
        clipped, _ = mask(
            src,
            [ward_geometry.__geo_interface__],
            crop=True,
            filled=False,
        )

    values = clipped[0].compressed()
    values = values[
        np.isfinite(values)
        & (values >= 0)
        & (values > INVALID_RASTER_THRESHOLD)
    ]

    if values.size == 0:
        return {
            "valid_pixel_count": 0,
            "mean": None,
            "median": None,
            "minimum": None,
            "maximum": None,
        }

    return {
        "valid_pixel_count": int(values.size),
        "mean": float(values.mean()),
        "median": float(np.median(values)),
        "minimum": float(values.min()),
        "maximum": float(values.max()),
    }
