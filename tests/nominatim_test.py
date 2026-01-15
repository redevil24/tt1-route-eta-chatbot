# test.py
import requests
import logging
from typing import List, Dict, Any

# ======================
# CONFIG
# ======================
NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"

LIMIT = 3
COUNTRY_CODES = "vn"
ACCEPT_LANGUAGE = "vi"

# viewbox TPHCM: left,bottom,right,top  (lon,lat,lon,lat)
VIEWBOX_TPHCM = "106.3567007,10.1399458,107.0276712,11.1603083"

USER_AGENT = "route-bot-test/1.0 (contact: nguyenminhanh56hv@gmail.com)"

# ======================
# LOGGING
# ======================
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s | %(message)s"
)
logger = logging.getLogger(__name__)

# ======================
# FUNCTION
# ======================
def geocode_nominatim(query: str) -> List[Dict[str, Any]]:
    """
    Call Nominatim with fixed params:
      q=<query>
      format=jsonv2
      limit=3
      addressdetails=1
      countrycodes=vn
      accept-language=vi
      viewbox=... (TPHCM)
      bounded=1

    Return raw JSON list (may be empty).
    """
    # TODO: implement: requests.get + params + headers(User-Agent)

    q = (query or "").strip()
    if not q:
        return []
    
    params = {
        "q": q,
        "format": "jsonv2",
        "limit": str(LIMIT),
        "addressdetails": "1",
        "countrycodes": COUNTRY_CODES,
        "accept-language": ACCEPT_LANGUAGE,
        "viewbox": VIEWBOX_TPHCM,
        "bounded": "1",
    }

    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/json",
    }

    try:
        resp = requests.get(
            NOMINATIM_URL,
            params=params,
            headers=headers,
            timeout=12,  # seconds
        )
        resp.raise_for_status()

        data = resp.json()
        if isinstance(data, list):
            return data

        # Defensive: if API returns non-list for some reason
        logger.warning("Nominatim unexpected JSON type: %s", type(data))
        return []

    except requests.exceptions.Timeout:
        logger.warning("Nominatim timeout for query=%r", q)
        return []
    except requests.exceptions.HTTPError as e:
        # 429 (Too Many Requests) can happen on public Nominatim
        status = getattr(e.response, "status_code", None)
        logger.warning("Nominatim HTTPError status=%s query=%r", status, q)
        return []
    except requests.exceptions.RequestException as e:
        logger.warning("Nominatim RequestException query=%r err=%s", q, e)
        return []
    except ValueError as e:
        # JSON decode error
        logger.warning("Nominatim JSON decode error query=%r err=%s", q, e)
        return []

# ======================
# TEST MAIN (SIMPLE)
# ======================
if __name__ == "__main__":
    query = "abcxs"

    results = geocode_nominatim(query)

    print(f"Query: {query}")
    print(f"Results count: {len(results)}\n")

    # In nguyên JSON list
    from pprint import pprint
    pprint(results)

