import datacraft
from datacraft_geo import *
from shapely.geometry import shape, Point


def test_bounded_lat_long():
    geo_filter = {"type": "Feature", "geometry": {"type": "Polygon", "coordinates": [
        [[23.0843, 53.1544], [23.0845, 53.1544], [23.0859, 53.1535], [23.0843, 53.1544]]]}}

    spec = {
        "lat": {
            "type": "geo.lat.clip",
            "config": {
                "geojson": geo_filter,
            }
        },
        "lon": {
            "type": "geo.long.clip",
            "config": {
                "geojson": geo_filter,
            }
        }
    }

    polygon = shape(geo_filter['geometry'])
    entries = datacraft.entries(spec, 100)
    for entry in entries:
        x = entry['lat']
        y = entry['lon']
        point = Point(x, y)
        assert not polygon.contains(point)

