import requests
import json
import logging
import geojson

from django.conf import settings


logger = logging.getLogger(__name__)


class ValhallaRouting():
    bicycle_types = [
        'Road',
        'Hybrid',
        'City',
        'Cross',
        'Mountain',
    ]

    def __init__(self, s_lat: float, s_lon: float, d_lat: float, d_lon: float) -> None:
        self.s_lat = s_lat
        self.s_lon = s_lon
        self.d_lat = d_lat
        self.d_lon = d_lon

    def query(self, bicycle_type='Road', r_timeout=2) -> dict:
        if bicycle_type not in self.bicycle_types:
            raise Exception(f"{bicycle_type} is not in the list of allowed bicycle_types from Vahalla")

        query = {
            'locations': [
                {
                    'lat': self.s_lat,
                    'lon': self.s_lon,
                },
                {
                    'lat': self.d_lat,
                    'lon': self.d_lon,
                },
            ],
            'costing': 'bicycle',
            'units': 'kilometers',
            'costing_options': {
                'bicycle': {
                    'bicycle_type': bicycle_type,
                    'use_hills': 0.5,
                },
            },
            'format': 'json',
        }

        try:
            r = requests.get(settings.VALHALLA_ROUTING_API_HOST + '?json=' + json.dumps(query), timeout=r_timeout)
        except requests.exceptions.Timeout:
            logger.warning(f"Query '{query}' did not finish within {r_timeout}")
            return {}

        route = {}

        if r.status_code == 200:
            routing_info = r.json()
            legs = routing_info.get('trip', {}).get('legs', {})

            if len(legs) != 1:
                raise Exception(f"Got: {legs} from Valhalla API but should only one inside the list")

            shape = legs[0].get('shape')

            route["length"] = routing_info.get('trip', {}).get('summary', {}).get('length')
            route["geojson"] = self.decode_shape(shape)

            return route

        return {}

    def decode_shape(self, encoded) -> list:
        # from: https://valhalla.github.io/valhalla/decoding/
        inv = 1.0 / 1e6
        decoded = []
        previous = [0, 0]
        i = 0
        # for each byte
        while i < len(encoded):
            # for each coord (lat, lon)
            ll = [0, 0]
            for j in [0, 1]:
                shift = 0
                byte = 0x20
                # keep decoding bytes until you have this coord
                while byte >= 0x20:
                    byte = ord(encoded[i]) - 63
                    i += 1
                    ll[j] |= (byte & 0x1f) << shift
                    shift += 5

                # get the final value adding the previous offset and remember it for the next
                ll[j] = previous[j] + (~(ll[j] >> 1) if ll[j] & 1 else (ll[j] >> 1))
                previous[j] = ll[j]
            # scale by the precision and chop off long coords also flip the positions so
            # its the far more standard lon,lat instead of lat,lon
            decoded.append([float('%.6f' % (ll[1] * inv)), float('%.6f' % (ll[0] * inv))])

        # hand back the list of coordinates
        return decoded
