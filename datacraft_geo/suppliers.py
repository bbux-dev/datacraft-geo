import logging
import random

import mgrs  # type: ignore
import utm  # type: ignore

from shapely.geometry import shape, Point

import datacraft

_log = logging.getLogger(__name__)


class _MgrsSupplier(datacraft.ValueSupplierInterface):
    def __init__(self, pair_supplier):
        self.pair_supplier = pair_supplier
        self.mgrs = mgrs.MGRS()

    def next(self, iteration: int):
        geo_pair = self.pair_supplier.next(iteration)
        return self.mgrs.toMGRS(geo_pair[0], geo_pair[1])


def mgrs_supplier(pair_supplier: datacraft.ValueSupplierInterface):
    """

    Args:
        pair_supplier: supplies tuples/list of (lat, long)

    Returns:
        a value supplier for the MGRS coordinates
    """
    return _MgrsSupplier(pair_supplier)


class _UtmSupplier(datacraft.ValueSupplierInterface):
    def __init__(self, pair_supplier, engine, lat_first):
        self.pair_supplier = pair_supplier
        self.engine = engine
        self.lat_first = lat_first

    def next(self, iteration: int):
        geo_pair = self.pair_supplier.next(iteration)
        if self.lat_first:
            lat, long = geo_pair
        else:
            long, lat = geo_pair
        try:
            easting, northing, zone_number, zone_letter = utm.from_latlon(lat, long)
        except utm.error.OutOfRangeError as err:
            _log.warning("Unable to convert %s: %s", str(geo_pair), str(err))
            raise err

        data = {
            "easting": easting,
            "northing": northing,
            "zone_number": zone_number,
            "zone_letter": zone_letter,
            "zn": zone_number,
            "zl": zone_letter,
        }
        return self.engine.process(data)


def utm_supplier(pair_supplier: datacraft.ValueSupplierInterface,
                 engine: datacraft.RecordProcessor,
                 lat_first: bool) -> datacraft.ValueSupplierInterface:
    """Creates a Value Supplier for utm coordinates

    Args:
        lat_first:
        pair_supplier: supplies tuples/list of (lat, long)
        engine: for processing the utm pieces into a string
        lat_first: if latitude is the first output of the pair_supplier

    Returns:
        a value supplier for the utm coordinates output according to the specified template
    """
    return _UtmSupplier(pair_supplier, engine, lat_first)


class _PointInBoundsSupplier(datacraft.ValueSupplierInterface):
    def __init__(self,
                 polygons: list,
                 pair_suppliers: list,
                 lat_first: bool = False,
                 join_with: str = None):
        self.polygons = polygons
        self.pair_suppliers = pair_suppliers
        self.lat_first = lat_first
        self.join_with = join_with

    def next(self, i: int):
        # sample one of our polygons
        idx = random.randrange(0, len(self.polygons))
        polygon = self.polygons[idx]
        pair_supplier = self.pair_suppliers[idx]

        x, y = pair_supplier.next(i)
        point = Point(x, y)
        count = 0
        # not super efficient, but gets the job done
        while not polygon.contains(point):
            x, y = pair_supplier.next(i)
            point = Point(x, y)
            count += 1
        _log.debug("%s points outside of bounds before hit", count)
        if self.lat_first:
            return_val = [y, x]
        else:
            return_val = [x, y]
        if self.join_with:
            return self.join_with.join([str(v) for v in return_val])
        return return_val


def point_in_bounds(geojson: dict, **kwargs):
    """Creates a value supplier that will use the polygons from the GeoJSON to create points in the bounds of the
    defined shapes.

    Args:
        geojson: to clip points by

    Keyword Args:
        join_with(bool): if the values should be joined by some given string, instead of returned as a list
        lat_first(bool): if latitude should be the first value in the list, default is longitude first

    Returns:
        A value supplier interface that returns the bounded points
    """
    feature_type = geojson.get('type')
    if feature_type == 'FeatureCollection':
        polygons = [shape(feature['geometry']) for feature in geojson['features']]
    elif feature_type == 'Feature':
        polygons = [shape(geojson['geometry'])]
    else:
        raise datacraft.SpecException('Invalid GeoJSON, must contain Feature or FeatureCollection')

    pair_suppliers = [_point_supplier_for_polygon(polygon) for polygon in polygons]
    return _PointInBoundsSupplier(polygons, pair_suppliers, **kwargs)


def _point_supplier_for_polygon(polygon):
    start_long, start_lat, end_long, end_lat = polygon.bounds
    return datacraft.suppliers.geo_pair(start_lat=start_lat,
                                        start_long=start_long,
                                        end_lat=end_lat,
                                        end_long=end_long,
                                        as_list=True)


class _IndexedPairValueSupplier(datacraft.ValueSupplierInterface):
    def __init__(self,
                 pair_supplier: datacraft.ValueSupplierInterface,
                 index: int):
        self.pair_supplier = pair_supplier
        self.index = index

    def next(self, iteration):
        pair = self.pair_supplier.next(iteration)
        return pair[self.index]


def lat_supplier(pair_supplier: datacraft.ValueSupplierInterface, **config):
    lat_first = config.get('lat_first', datacraft.registries.get_default('geo_lat_first'))
    if lat_first:
        return _IndexedPairValueSupplier(pair_supplier, index=0)
    return _IndexedPairValueSupplier(pair_supplier, index=1)


def long_supplier(pair_supplier: datacraft.ValueSupplierInterface, **config):
    lat_first = config.get('lat_first', datacraft.registries.get_default('geo_lat_first'))
    if lat_first:
        return _IndexedPairValueSupplier(pair_supplier, index=1)
    return _IndexedPairValueSupplier(pair_supplier, index=0)
