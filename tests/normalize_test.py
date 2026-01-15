from typing import List, Dict, Any
import json

def build_label(raw_item: Dict[str, Any]) -> str:
    """
    Build short label from raw_item using FINAL rule (name/display_name + addressdetails parts).
    """
    # TODO: implement FINAL label rule
    name = (raw_item.get("name") or "").strip()
    display_name = (raw_item.get("display_name") or "").strip()

    if name:
        base_name = name
    else:
        # Fallback: first segment of display_name
        base_name = display_name.split(",")[0].strip() if display_name else ""

    if not base_name:
        # Worst-case fallback
        base_name = "Không rõ"    

    address = raw_item.get("address") or {}
    if not isinstance(address, dict):
        address = {}

    parts: List[str] = []

     # ---- Part 1: house_number + road ----
    hn = (address.get("house_number") or "").strip()
    road = (address.get("road") or "").strip()

    # Drop road if it duplicates base_name (exact match as you chốt)
    if road and road == base_name:
        road = ""
    
    part1 = ""
    if hn and road:
        part1 = f"{hn} {road}"
    elif hn and not road:
        part1 = hn
    elif (not hn) and road:
        part1 = road
    
    if part1.strip():
        parts.append(part1.strip())

    # ---- Part 2: neighbourhood ----
    nb = (address.get("neighbourhood") or "").strip()
    if nb:
        parts.append(nb)

    # ---- Part 3: suburb ----
    sb = (address.get("suburb") or "").strip()
    if sb:
        parts.append(sb)
    
    # ---- Compose label (default N=3) ----
    if not parts:
        label = base_name
    else:
        label = f"{base_name} — {', '.join(parts[:3])}"

    # ---- Beautify (final) ----
    label = label.replace("Phường ", "P. ")
    label = label.replace("Khu phố ", "KP ")
    label = label.replace("Đường ", "")

    # Optional: collapse multiple spaces after replacements
    # label = " ".join(label.split()).strip()

    # Optional length guard (enable if you want later)
    # MAX_LEN = 55
    # if len(label) > MAX_LEN:
    #     label = label[: MAX_LEN - 1].rstrip() + "…"

    return label


def normalize_candidates(raw_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Convert raw Nominatim items -> Candidate objects (top LIMIT items):
    Candidate = {
        "lat": float,
        "lon": float,
        "label": str,
        "display_name": str
    }

    Assumptions:
    - raw_list is a list returned by geocode_nominatim()
    - build_label(raw_item) already applies N=3 and beautify
    """
    # TODO: implement: parse lat/lon float + label + display_name
    candidates: List[Dict[str, Any]] = []
    if not raw_list:
        return candidates

    for item in raw_list:
        try:
            lat_str = item.get("lat")
            lon_str = item.get("lon")
            if lat_str is None or lon_str is None:
                continue

            lat = float(lat_str)
            lon = float(lon_str)

            display_name = (item.get("display_name") or "").strip()
            label = build_label(item).strip()

            if not label:
                label = (display_name.split(",")[0].strip() if display_name else "Không rõ")

            candidates.append(
                {
                    "lat": lat,
                    "lon": lon,
                    "label": label,
                    "display_name": display_name,
                }
            )
        except (ValueError, TypeError):
            continue

    return candidates


# ======================
# PASTE RAW LIST HERE
# ======================
RAW_LIST: List[Dict[str, Any]] = [
    # DÁN list of dict từ Nominatim vào đây
    {
    "place_id": 239870893,
    "licence": "Data © OpenStreetMap contributors, ODbL 1.0. http://osm.org/copyright",
    "osm_type": "node",
    "osm_id": 11868700660,
    "lat": "10.7958270",
    "lon": "106.7225902",
    "category": "highway",
    "type": "bus_stop",
    "place_rank": 30,
    "importance": 0.000067033646143236,
    "addresstype": "highway",
    "name": "Vinhomes Central Park - Tòa nhà Landmark 81",
    "display_name": "Vinhomes Central Park - Tòa nhà Landmark 81, Trần Trọng Kim, Khu phố 48, Phường Thạnh Mỹ Tây, Thành phố Thủ Đức, Thành phố Hồ Chí Minh, 71108, Việt Nam",
    "address": {
      "highway": "Vinhomes Central Park - Tòa nhà Landmark 81",
      "road": "Trần Trọng Kim",
      "neighbourhood": "Khu phố 48",
      "suburb": "Phường Thạnh Mỹ Tây",
      "city": "Thành phố Thủ Đức",
      "ISO3166-2-lvl4": "VN-SG",
      "postcode": "71108",
      "country": "Việt Nam",
      "country_code": "vn"
    },
    "boundingbox": [
      "10.7957770",
      "10.7958770",
      "106.7225402",
      "106.7226402"
    ]
  },
  {
    "place_id": 239763912,
    "licence": "Data © OpenStreetMap contributors, ODbL 1.0. http://osm.org/copyright",
    "osm_type": "node",
    "osm_id": 9585001093,
    "lat": "10.7950845",
    "lon": "106.7219139",
    "category": "shop",
    "type": "yes",
    "place_rank": 30,
    "importance": 0.000067033646143236,
    "addresstype": "shop",
    "name": "Cửa Hàng Innisfree - Vincom Landmark 81",
    "display_name": "Cửa Hàng Innisfree - Vincom Landmark 81, Trần Trọng Kim, Vinhomes Central Park, Phường Thạnh Mỹ Tây, Thành phố Thủ Đức, Thành phố Hồ Chí Minh, 71108, Việt Nam",
    "address": {
      "shop": "Cửa Hàng Innisfree - Vincom Landmark 81",
      "road": "Trần Trọng Kim",
      "residential": "Vinhomes Central Park",
      "suburb": "Phường Thạnh Mỹ Tây",
      "city": "Thành phố Thủ Đức",
      "ISO3166-2-lvl4": "VN-SG",
      "postcode": "71108",
      "country": "Việt Nam",
      "country_code": "vn"
    },
    "boundingbox": [
      "10.7950345",
      "10.7951345",
      "106.7218639",
      "106.7219639"
    ]
  },
  {
    "place_id": 239452564,
    "licence": "Data © OpenStreetMap contributors, ODbL 1.0. http://osm.org/copyright",
    "osm_type": "way",
    "osm_id": 306996390,
    "lat": "10.7969577",
    "lon": "106.7504543",
    "category": "landuse",
    "type": "residential",
    "place_rank": 24,
    "importance": 0.0800670336461433,
    "addresstype": "residential",
    "name": "PetroVietnam Landmark",
    "display_name": "PetroVietnam Landmark, Phường Bình Trưng, Thành phố Thủ Đức, Thành phố Hồ Chí Minh, Việt Nam",
    "address": {
      "residential": "PetroVietnam Landmark",
      "suburb": "Phường Bình Trưng",
      "city": "Thành phố Thủ Đức",
      "ISO3166-2-lvl4": "VN-SG",
      "country": "Việt Nam",
      "country_code": "vn"
    },
    "boundingbox": [
      "10.7965111",
      "10.7973746",
      "106.7496249",
      "106.7512864"
    ]
  }
]


# ======================
# RUN NORMALIZATION
# ======================
def main():
    print("=== RAW INPUT ===")
    # print(json.dumps(RAW_LIST, ensure_ascii=False, indent=2))

    print("\n=== NORMALIZED CANDIDATES ===")
    candidates = normalize_candidates(RAW_LIST)
    print(json.dumps(candidates, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()