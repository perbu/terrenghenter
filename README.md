# terrenghenter

CLI for å hente norske terrengdata fra høydedata.no. Gir deg GeoTIFF som kan brukes med TouchTerrain, Mapa, eller andre verktøy.

## Installasjon

```bash
uv sync
```

## Bruk

```bash
# Hent 1x1km rundt et punkt
terrenghenter fetch --lat 59.9639 --lon 10.6683 --width 1000 --height 1000 -o terrain.tif

# Hent for en bounding box
terrenghenter fetch-bbox --min-lat 59.9 --min-lon 10.6 --max-lat 60.0 --max-lon 10.8 -o area.tif

# Vis info om en fil
terrenghenter info terrain.tif
```

## Parametre

- `--resolution` - Oppløsning i meter/piksel (standard: 1.0)
- `--width/--height` - Størrelse i meter
- `-o/--output` - Utfil (standard: terrain.tif)

## Datakilde

Data hentes fra Kartverkets høydedata.no (DTM ImageServer). Dataene er fritt tilgjengelige under NLOD/CC BY 4.0.

## Lisens

BSD 2-Clause
