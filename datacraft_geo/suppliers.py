import logging

import mgrs  # type: ignore
import utm  # type: ignore

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
