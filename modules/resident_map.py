import os
from dotenv import load_dotenv
import folium
import numpy as np
from folium.raster_layers import ImageOverlay
from matplotlib import colormaps
from matplotlib.colors import Normalize, to_hex
from rasterio.features import geometry_mask
from rasterio.transform import array_bounds

from modules.data_loader import load_wards, load_population_raster
load_dotenv()
CARTO_API_KEY = os.getenv("CARTO_API_KEY")


def create_resident_map():
    """Create the first interactive Mangaluru resident map."""
    wards = load_wards()
    raster = load_population_raster()

    center = [12.9141, 74.8560]

    m = folium.Map(
        location=center,
        zoom_start=12,
        tiles=None,
        control_scale=True,
    )


    if CARTO_API_KEY:
        folium.TileLayer(
            tiles=(
                "https://basemaps.cartocdn.com/"
                "rastertiles/voyager/{z}/{x}/{y}.png"
                f"?key={CARTO_API_KEY}"
            ),
            attr="© OpenStreetMap contributors © CARTO",
            name="CARTO Voyager",
            overlay=False,
            control=True,
        ).add_to(m)
    else:
        raise ValueError(
            "CARTO_API_KEY was not found. Check your .env file."
        )

    # Display values only for valid pixels inside ward boundaries.
    inside_wards = geometry_mask(
        wards.geometry.__geo_interface__["features"]
        if False else [geom.__geo_interface__ for geom in wards.geometry],
        out_shape=raster["data"].shape,
        transform=raster["transform"],
        invert=True,
    )

    data = raster["data"]
    valid_inside = raster["valid_mask"] & inside_wards

    if valid_inside.any():
        low, high = np.nanpercentile(data[valid_inside], [2, 98])

        if high <= low:
            high = low + 1

        normalized = Normalize(vmin=low, vmax=high, clip=True)
        cmap = colormaps["RdYlGn_r"]

        rgba = np.zeros((*data.shape, 4), dtype=np.uint8)
        scaled = np.zeros(data.shape, dtype=float)
        scaled[valid_inside] = normalized(data[valid_inside])

        colors = cmap(scaled)
        rgba[..., :3] = (colors[..., :3] * 255).astype(np.uint8)
        rgba[..., 3] = np.where(valid_inside, 180, 0).astype(np.uint8)
        print("Non-transparent pixels:", int(np.count_nonzero(rgba[..., 3])))

        west, south, east, north = array_bounds(
            data.shape[0],
            data.shape[1],
            raster["transform"],
        )

        ImageOverlay(
            image=rgba,
            bounds=[[south, west], [north, east]],
            opacity=0.55,
            name="Population raster (provisional)",
            interactive=False,
            cross_origin=False,
            pixelated=False,
            zindex=1,
        ).add_to(m)

        legend = f"""
        <div style="
            position: fixed; bottom: 28px; left: 28px; z-index: 9999;
            background: white; padding: 10px 12px;
            border: 1px solid #aaa; border-radius: 6px;
            font-size: 12px; max-width: 230px;">
            <b>Population raster — provisional</b><br>
            Relative display scale: {low:.0f}–{high:.0f}<br>
            <span style="color:#666">
            Units and reference year still require verification.
            </span>
        </div>
        """
        m.get_root().html.add_child(folium.Element(legend))

    def ward_style(_feature):
        return {
            "fillColor": "#3388ff",
            "color": "#1f4e79",
            "weight": 1.5,
            "fillOpacity": 0.04,
        }

    folium.GeoJson(
        wards,
        name="Mangaluru wards",
        style_function=ward_style,
        tooltip=folium.GeoJsonTooltip(
            fields=["KGISWardNo", "KGISWardNa"],
            aliases=["Ward number:", "Ward name:"],
            sticky=True,
        ),
    ).add_to(m)

    folium.LayerControl(collapsed=False).add_to(m)
    return m
