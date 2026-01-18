"""CLI for terrenghenter."""

from pathlib import Path

import click

from .api import BoundingBox, HoydedataClient


@click.group()
@click.version_option()
def cli():
    """Fetch Norwegian terrain data from høydedata.no."""
    pass


@cli.command()
@click.option("--lat", type=float, required=True, help="Center latitude (WGS84)")
@click.option("--lon", type=float, required=True, help="Center longitude (WGS84)")
@click.option("--width", type=float, default=1000, help="Width in meters (default: 1000)")
@click.option("--height", type=float, default=1000, help="Height in meters (default: 1000)")
@click.option("--resolution", type=float, default=1.0, help="Resolution in meters/pixel (default: 1.0)")
@click.option("-o", "--output", type=click.Path(), default="terrain.tif", help="Output file path")
def fetch(lat: float, lon: float, width: float, height: float, resolution: float, output: str):
    """Fetch terrain data centered on a point.

    Example:

        terrenghenter fetch --lat 59.9639 --lon 10.6683 --width 1000 --height 1000 -o terrain.tif
    """
    bbox = BoundingBox.from_center_and_size(lon, lat, width, height)

    click.echo(f"Fetching {width}x{height}m area centered at ({lat}, {lon})")
    click.echo(f"Resolution: {resolution}m/pixel")
    click.echo(f"UTM33 bbox: {bbox.to_bbox_string()}")

    with HoydedataClient(resolution=resolution) as client:
        output_path = client.fetch_dtm(bbox, Path(output))

    click.echo(f"Saved to: {output_path}")


@cli.command()
@click.option("--min-lat", type=float, required=True, help="Min latitude (SW corner)")
@click.option("--min-lon", type=float, required=True, help="Min longitude (SW corner)")
@click.option("--max-lat", type=float, required=True, help="Max latitude (NE corner)")
@click.option("--max-lon", type=float, required=True, help="Max longitude (NE corner)")
@click.option("--resolution", type=float, default=1.0, help="Resolution in meters/pixel (default: 1.0)")
@click.option("-o", "--output", type=click.Path(), default="terrain.tif", help="Output file path")
def fetch_bbox(min_lat: float, min_lon: float, max_lat: float, max_lon: float,
               resolution: float, output: str):
    """Fetch terrain data for a bounding box.

    Example:

        terrenghenter fetch-bbox --min-lat 59.9 --min-lon 10.6 --max-lat 60.0 --max-lon 10.8 -o area.tif
    """
    bbox = BoundingBox.from_wgs84(min_lon, min_lat, max_lon, max_lat)

    click.echo(f"Fetching area from ({min_lat}, {min_lon}) to ({max_lat}, {max_lon})")
    click.echo(f"Resolution: {resolution}m/pixel")
    click.echo(f"Area: {bbox.width:.0f}x{bbox.height:.0f}m")
    click.echo(f"UTM33 bbox: {bbox.to_bbox_string()}")

    with HoydedataClient(resolution=resolution) as client:
        output_path = client.fetch_dtm(bbox, Path(output))

    click.echo(f"Saved to: {output_path}")


@cli.command()
@click.argument("tiff_file", type=click.Path(exists=True))
def info(tiff_file: str):
    """Show information about a terrain GeoTIFF file.

    Example:

        terrenghenter info terrain.tif
    """
    import rasterio

    with rasterio.open(tiff_file) as src:
        click.echo(f"File: {tiff_file}")
        click.echo(f"Size: {src.width}x{src.height} pixels")
        click.echo(f"CRS: {src.crs}")
        click.echo(f"Bounds: {src.bounds}")
        click.echo(f"Resolution: {src.res[0]:.2f}x{src.res[1]:.2f}m")

        data = src.read(1)
        click.echo(f"Elevation range: {data.min():.1f}m to {data.max():.1f}m")


def main():
    cli()


if __name__ == "__main__":
    main()
