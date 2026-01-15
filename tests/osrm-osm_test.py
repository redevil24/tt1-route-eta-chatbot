# test.py
import logging
from typing import Tuple, Dict, Any
import requests

# ======================
# CONFIG
# ======================
OSRM_URL = "https://router.project-osrm.org/route/v1/driving"
USER_AGENT = "osrm-test/1.0 (contact: test@example.com)"

# ======================
# LOGGING
# ======================
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def osrm_route(from_coord: Tuple[float, float], to_coord: Tuple[float, float]) -> Dict[str, Any]:
    """
    Call OSRM: /route/v1/driving/lon,lat;lon,lat?overview=false
    Return dict with distance_m, duration_s.
    """
    # TODO: implement OSRM request + parse routes[0]
    from_lat, from_lon = from_coord
    to_lat, to_lon = to_coord

    url = f"{OSRM_URL}/{from_lon},{from_lat};{to_lon},{to_lat}"
    params = {
        "overview": "false",
    }
    headers = {
        "Accept": "application/json",
        "User-Agent": USER_AGENT,  # not required by OSRM demo but harmless
    }

    try:
        resp = requests.get(url, params=params, headers=headers, timeout=12)
        resp.raise_for_status()
        data = resp.json()

        routes = data.get("routes") or []
        if not routes:
            return {}

        r0 = routes[0] or {}
        distance_m = r0.get("distance")
        duration_s = r0.get("duration")

        if distance_m is None or duration_s is None:
            return {}

        return {
            "distance_m": float(distance_m),
            "duration_s": float(duration_s),
        }

    except requests.exceptions.Timeout:
        logger.warning("OSRM timeout url=%s", url)
        return {}
    except requests.exceptions.HTTPError as e:
        status = getattr(e.response, "status_code", None)
        logger.warning("OSRM HTTPError status=%s url=%s", status, url)
        return {}
    except requests.exceptions.RequestException as e:
        logger.warning("OSRM RequestException url=%s err=%s", url, e)
        return {}
    except ValueError as e:
        logger.warning("OSRM JSON decode error url=%s err=%s", url, e)
        return {}


def build_osm_directions_link(from_coord: Tuple[float, float], to_coord: Tuple[float, float]) -> str:
    """
    Build OSM directions link:
    https://www.openstreetmap.org/directions?engine=fossgis_osrm_car&route=lat1,lon1;lat2,lon2
    """
    # TODO: implement
    from_lat, from_lon = from_coord
    to_lat, to_lon = to_coord

    # Keep a reasonable precision for URLs
    a = f"{from_lat:.6f},{from_lon:.6f}"
    b = f"{to_lat:.6f},{to_lon:.6f}"

    return f"https://www.openstreetmap.org/directions?engine=fossgis_osrm_car&route={a};{b}"


# ======================
# MAIN – bạn sửa tọa độ ở đây
# ======================
if __name__ == "__main__":
    from_coord = (10.7765300, 106.7009810)  # Quận 1
    to_coord   = (10.8230989, 106.6296638)  # Sân bay TSN


    result = osrm_route(from_coord, to_coord)
    print(result)

    link = build_osm_directions_link(from_coord, to_coord)
    print(link)