import pytest
import datacraft
from shapely.geometry import shape, Point
import mgrs
import utm


@pytest.fixture()
def geo_filter():
    return {"type": "Feature", "geometry": {"type": "Polygon", "coordinates": [
        [[23.0843, 53.1544], [23.0845, 53.1544], [23.0859, 53.1535], [23.0843, 53.1544]]]}}


def test_bounded_lat_long(geo_filter):
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
    entries = datacraft.entries(spec, 100, enforce_schema=True)
    for entry in entries:
        x = entry['lat']
        y = entry['lon']
        point = Point(x, y)
        assert not polygon.contains(point)


def test_bounded_mgrs(geo_filter):
    spec = {
        "mgrs_clipped": {
            "type": "geo.mgrs",
            "config": {
                "geojson": geo_filter,
            }
        }
    }

    polygon = shape(geo_filter['geometry'])
    entries = datacraft.entries(spec, 100, enforce_schema=True)
    for entry in entries:
        mgrs_str = entry['mgrs_clipped']
        x, y = mgrs.MGRS().toLatLon(mgrs_str)
        point = Point(x, y)
        assert not polygon.contains(point)


def test_bounded_utm(geo_filter):
    spec = {
        "utm_clipped": {
            "type": "geo.utm",
            "config": {
                "geojson": geo_filter,
            }
        }
    }

    polygon = shape(geo_filter['geometry'])
    entries = datacraft.entries(spec, 100, enforce_schema=True)
    for entry in entries:
        utm_str = entry['utm_clipped']
        zone_number, zone_letter, easting, northing = utm_str.split(' ')
        x, y = utm.to_latlon(float(easting),
                             float(northing),
                             int(zone_number),
                             zone_letter)
        point = Point(x, y)
        assert not polygon.contains(point)


def _spec_with_geojson(type_name, geojson):
    return {
        "geo": {
            "type": type_name,
            "config": {
                "geojson": geojson,
            }
        }
    }


invalid_geojson_specs = [
    _spec_with_geojson('geo.lat.clip', None),
    _spec_with_geojson('geo.long.clip', ''),
    _spec_with_geojson('geo.pair.clip', {}),
    _spec_with_geojson('geo.utm', '/path/does/not/exist.geo.json'),
    _spec_with_geojson('geo.mgrs', 'does.not.exist.json'),
]


@pytest.mark.parametrize("spec", invalid_geojson_specs)
def test_invalid_geojson(spec):
    with pytest.raises(datacraft.SpecException):
        datacraft.entries(spec, 1)
