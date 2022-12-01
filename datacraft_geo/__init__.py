import logging

import datacraft
import datacraft._registered_types.common as common

from . import suppliers

_GEO_UTM_TEMPLATE = "geo_utm_template"

_MGRS_KEY = 'geo.mgrs'
_UTM_KEY = 'geo.utm'

_log = logging.getLogger(__name__)


def load_custom():
    """ called by datacraft entrypoint loader """
    @datacraft.registry.schemas(_MGRS_KEY)
    def _get_mgrs_schema():
        """ get the schema for mgrs type """
        return {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "$id": "https://github.com/bbux-dev/datacraft-geo/schemas/mgrs.schema.json",
            "type": "object",
            "properties": {
                "type": {"type": "string", "pattern": "^geo.mgrs$"},
                "config": {
                    "type": "object",
                    "properties": {
                        "start_lat": {"type": "number", "minimum": -90, "maximum": 90},
                        "end_lat": {"type": "number", "minimum": -90, "maximum": 90},
                        "start_long": {"type": "number", "minimum": -180, "maximum": 180},
                        "end_long": {"type": "number", "minimum": -180, "maximum": 180},
                    },
                    "additionalProperties": False
                }
            }
        }

    @datacraft.registry.types(_MGRS_KEY)
    def _configure_mgrs_supplier(field_spec, loader: datacraft.Loader):
        """ configure the supplier for mgrs types """
        pair_supplier = _get_pair_supplier(field_spec, loader)
        return suppliers.mgrs_supplier(pair_supplier)

    @datacraft.registry.usage(_MGRS_KEY)
    def _configure_mgrs_usage():
        """ configure the usage for mgrs types """
        example = {
            "bound_mgrs": {
                "type": "geo.mgrs",
                "config": {
                    "start_lat": 49.5,
                    "end_lat": 50.5,
                    "start_long": 49.5,
                    "end_long": 40.5
                }
            }
        }
        return common.standard_example_usage(example, 3)

    @datacraft.registry.schemas(_UTM_KEY)
    def _get_utm_schema():
        """ get the schema for utm type """
        return {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "$id": "https://github.com/bbux-dev/datacraft-geo/schemas/utm.schema.json",
            "type": "object",
            "properties": {
                "type": {"type": "string", "pattern": "^geo.utm$"},
                "config": {
                    "type": "object",
                    "properties": {
                        "template": {"type": "string"},
                        "start_lat": {
                            "type": "number", "minimum": -80, "maximum": 84,
                            "description": ""
                        },
                        "end_lat": {
                            "type": "number", "minimum": -80, "maximum": 84
                        },
                        "start_long": {"type": "number", "minimum": -180, "maximum": 180},
                        "end_long": {"type": "number", "minimum": -180, "maximum": 180},
                    },
                    "additionalProperties": False
                }
            }
        }

    @datacraft.registry.defaults(_GEO_UTM_TEMPLATE)
    def _default_utm_template():
        return "{{ zone_number }} {{ zone_letter }} {{ easting | int }} {{ northing | int }}"

    @datacraft.registry.types(_UTM_KEY)
    def _configure_utm_supplier(field_spec, loader: datacraft.Loader):
        """ configure the supplier for utm types """
        config = datacraft.utils.load_config(field_spec, loader)
        if 'as_list' not in config or config['as_list'] is False:
            config['as_list'] = True
        if 'start_lat' not in config or config['start_lat'] < -80.0:
            config['start_lat'] = -80
        if 'end_lat' not in config or config['end_lat'] > 84:
            config['end_lat'] = 84
        lat_first = datacraft.utils.is_affirmative(
            'lat_first', config, datacraft.registries.get_default('geo_lat_first'))
        pair_supplier = datacraft.suppliers.geo_pair(**config)
        template = config.get('template', datacraft.registries.get_default(_GEO_UTM_TEMPLATE))
        engine = datacraft.outputs.processor(template=template)
        return suppliers.utm_supplier(pair_supplier, engine, lat_first)

    @datacraft.registry.usage(_MGRS_KEY)
    def _configure_utm_usage():
        """ configure the usage for utm types """
        example = {
            "custom_format": {
                "type": "geo.utm",
                "config": {
                    "template": "{{ zone_number }}{{ zone_letter }} {{ easting | int }}/{{ northing | int }}"
                }
            }
        }
        return common.standard_example_usage(example, 3)

    def _get_pair_supplier(field_spec, loader):
        config = datacraft.utils.load_config(field_spec, loader)
        if 'as_list' not in config or config['as_list'] is False:
            config['as_list'] = True
        pair_supplier = datacraft.suppliers.geo_pair(**config)
        return pair_supplier
