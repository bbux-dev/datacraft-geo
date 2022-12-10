import pytest

import datacraft

import datacraft_geo.suppliers as impl


@pytest.fixture()
def pair_supplier():
    return datacraft.suppliers.geo_pair(as_list=True, start_lat=-80, end_lat=84)


def test_basic_mgrs(pair_supplier):
    supplier = impl.mgrs_supplier(pair_supplier, False)

    val = supplier.next(0)

    assert len(val) <= 15


def test_basic_utm(pair_supplier):
    template = "{{ zone_number }}{{ zone_letter }} {{ easting | int }}/{{ northing | int }}"
    engine = datacraft.outputs.processor(template=template)
    supplier = impl.utm_supplier(pair_supplier, engine, False)

    val = supplier.next(0)

    assert len(val) <= 19


def test_mgrs_from_spec():
    spec = {
        "mgrs": {
            "type": "geo.mgrs"
        }
    }
    one = datacraft.entries(spec, 1, enforce_schema=True)[0]
    assert len(one['mgrs']) <= 15


def test_utm_from_spec():
    spec = {
        "utm": {
            "type": "geo.utm"
        }
    }
    one = datacraft.entries(spec, 1)[0]
    assert len(one['utm']) <= 19
