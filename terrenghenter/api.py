"""Client for høydedata.no ArcGIS REST API."""

from dataclasses import dataclass
from pathlib import Path

import httpx
from pyproj import CRS, Transformer


# høydedata.no uses EPSG:25833 (ETRS89 / UTM zone 33N)
HOYDEDATA_CRS = CRS.from_epsg(25833)
WGS84_CRS = CRS.from_epsg(4326)

# API endpoints
BASE_URL = "https://hoydedata.no/arcgis/rest/services"
DTM_ENDPOINT = f"{BASE_URL}/DTM/ImageServer/exportImage"

# Service limits
MAX_IMAGE_SIZE = 15000  # pixels per dimension


@dataclass
class BoundingBox:
    """Bounding box in UTM33 coordinates (EPSG:25833)."""

    min_x: float
    min_y: float
    max_x: float
    max_y: float

    @classmethod
    def from_wgs84(cls, min_lon: float, min_lat: float, max_lon: float, max_lat: float) -> "BoundingBox":
        """Create bounding box from WGS84 coordinates (lat/lon)."""
        transformer = Transformer.from_crs(WGS84_CRS, HOYDEDATA_CRS, always_xy=True)
        min_x, min_y = transformer.transform(min_lon, min_lat)
        max_x, max_y = transformer.transform(max_lon, max_lat)
        return cls(min_x=min_x, min_y=min_y, max_x=max_x, max_y=max_y)

    @classmethod
    def from_center_and_size(cls, center_lon: float, center_lat: float,
                              width_m: float, height_m: float) -> "BoundingBox":
        """Create bounding box from center point (WGS84) and size in meters."""
        transformer = Transformer.from_crs(WGS84_CRS, HOYDEDATA_CRS, always_xy=True)
        center_x, center_y = transformer.transform(center_lon, center_lat)
        half_w = width_m / 2
        half_h = height_m / 2
        return cls(
            min_x=center_x - half_w,
            min_y=center_y - half_h,
            max_x=center_x + half_w,
            max_y=center_y + half_h,
        )

    @property
    def width(self) -> float:
        """Width in meters."""
        return self.max_x - self.min_x

    @property
    def height(self) -> float:
        """Height in meters."""
        return self.max_y - self.min_y

    def to_bbox_string(self) -> str:
        """Format as bbox parameter for API."""
        return f"{self.min_x},{self.min_y},{self.max_x},{self.max_y}"


class HoydedataClient:
    """Client for fetching terrain data from høydedata.no."""

    def __init__(self, resolution: float = 1.0):
        """
        Initialize client.

        Args:
            resolution: Desired resolution in meters per pixel.
        """
        self.resolution = resolution
        self._client = httpx.Client(timeout=60.0)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self._client.close()

    def close(self):
        self._client.close()

    def _calculate_image_size(self, bbox: BoundingBox) -> tuple[int, int]:
        """Calculate image dimensions based on bbox and resolution."""
        width = int(bbox.width / self.resolution)
        height = int(bbox.height / self.resolution)

        # Clamp to API limits
        if width > MAX_IMAGE_SIZE or height > MAX_IMAGE_SIZE:
            scale = MAX_IMAGE_SIZE / max(width, height)
            width = int(width * scale)
            height = int(height * scale)

        return width, height

    def fetch_dtm(self, bbox: BoundingBox, output_path: Path) -> Path:
        """
        Fetch DTM data for the given bounding box.

        Args:
            bbox: Bounding box in UTM33 coordinates.
            output_path: Path to save the GeoTIFF file.

        Returns:
            Path to the saved file.
        """
        width, height = self._calculate_image_size(bbox)

        params = {
            "bbox": bbox.to_bbox_string(),
            "bboxSR": "25833",
            "imageSR": "25833",
            "size": f"{width},{height}",
            "format": "tiff",
            "pixelType": "F32",  # 32-bit float for elevation data
            "interpolation": "RSP_BilinearInterpolation",
            "f": "image",
        }

        response = self._client.get(DTM_ENDPOINT, params=params)
        response.raise_for_status()

        # Verify we got a TIFF
        content_type = response.headers.get("content-type", "")
        if "tiff" not in content_type.lower() and "image" not in content_type.lower():
            raise ValueError(f"Unexpected response type: {content_type}")

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(response.content)

        return output_path

    def fetch_dtm_wgs84(self, min_lon: float, min_lat: float,
                        max_lon: float, max_lat: float, output_path: Path) -> Path:
        """
        Fetch DTM data using WGS84 coordinates.

        Args:
            min_lon, min_lat: Southwest corner (longitude, latitude).
            max_lon, max_lat: Northeast corner (longitude, latitude).
            output_path: Path to save the GeoTIFF file.

        Returns:
            Path to the saved file.
        """
        bbox = BoundingBox.from_wgs84(min_lon, min_lat, max_lon, max_lat)
        return self.fetch_dtm(bbox, output_path)
