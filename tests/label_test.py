# test.py
from typing import Dict, Any, List

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

# ======================
# MAIN – DÁN DICT VÀO ĐÂY
# ======================
if __name__ == "__main__":

    raw_item =   {
    "place_id": 239501500,
    "licence": "Data © OpenStreetMap contributors, ODbL 1.0. http://osm.org/copyright",
    "osm_type": "node",
    "osm_id": 3116882984,
    "lat": "10.7713016",
    "lon": "106.6578284",
    "category": "highway",
    "type": "bus_stop",
    "place_rank": 30,
    "importance": 0.000067033646143236,
    "addresstype": "highway",
    "name": "Đại học Bách Khoa",
    "display_name": "Đại học Bách Khoa, Lý Thường Kiệt, Khu phố 1, Phường Phú Thọ, Thành phố Thủ Đức, Thành phố Hồ Chí Minh, 72117, Việt Nam",
    "address": {
      "highway": "Đại học Bách Khoa",
      "road": "Lý Thường Kiệt",
      "neighbourhood": "Khu phố 1",
      "suburb": "Phường Phú Thọ",
      "city": "Thành phố Thủ Đức",
      "ISO3166-2-lvl4": "VN-SG",
      "postcode": "72117",
      "country": "Việt Nam",
      "country_code": "vn"
    },
    "boundingbox": [
      "10.7712516",
      "10.7713516",
      "106.6577784",
      "106.6578784"
    ]
  }
    print(build_label(raw_item))