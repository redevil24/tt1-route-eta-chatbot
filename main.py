#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
TT1 - Route & ETA Chatbot (MVP)
- Telegram (python-telegram-bot)
- FSM: FROM_TEXT -> FROM_PICK -> TO_TEXT -> TO_PICK -> MODE -> END
- Geocode: Nominatim (bounded HCM, limit=3, addressdetails=1)
- Routing: OSRM public (driving)
- Map link: OpenStreetMap Directions (engine=fossgis_osrm_car)

Author: Nguyen Minh Anh
"""

import logging
import os
import re
from typing import Any, Dict, List, Optional, Tuple

import requests
from dotenv import load_dotenv
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

# =========================
# Logging
# =========================
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

# =========================
# Load token
# =========================
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise RuntimeError("BOT_TOKEN not found. Check your .env file.")

# =========================
# States
# =========================
FROM_TEXT, FROM_PICK, TO_TEXT, TO_PICK, MODE = range(5)

# =========================
# Config (API)
# =========================
NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
OSRM_URL = "https://router.project-osrm.org/route/v1/driving"

# NOTE: Keep your viewbox as you have "chốt" (we'll handle ordering later if needed)
VIEWBOX_TPHCM = "106.3567007,10.1399458,107.0276712,11.1603083"
COUNTRY_CODES = "vn"
LIMIT = 3
ACCEPT_LANGUAGE = "vi"

# User-Agent required by Nominatim usage policy
USER_AGENT = "tt1-route-bot/1.0 (demo; contact: nguyenminhanh56hv@gmail.com)"

# =========================
# Context helpers (10 keys)
# =========================
def init_context(user_data: Dict[str, Any]) -> None:
    """Reset context.user_data to default (10 keys)."""
    user_data.clear()
    user_data.update(
        {
            "from_text": None,
            "from_candidates": [],
            "from_coord": None,
            "from_label": None,
            "to_text": None,
            "to_candidates": [],
            "to_coord": None,
            "to_label": None,
            "mode": None,         # set ONLY after user chooses CAR or SKIP
            "route_result": None, # optional cache
        }
    )

def clear_from(user_data: Dict[str, Any]) -> None:
    user_data["from_text"] = None
    user_data["from_candidates"] = []
    user_data["from_coord"] = None
    user_data["from_label"] = None

def clear_to(user_data: Dict[str, Any]) -> None:
    user_data["to_text"] = None
    user_data["to_candidates"] = []
    user_data["to_coord"] = None
    user_data["to_label"] = None

# =========================
# Commands (outside flow)
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/start - intro (outside flow)."""
    await update.message.reply_text(
        "👋 *Xin chào!*\n"
        "Mình là bot hỗ trợ tìm đường và ước tính thời gian đến (ETA) tại TPHCM.\n\n"
        "📌 *Cách dùng nhanh:*\n"
        "- Gõ /route để bắt đầu\n"
        "- Gõ /help để xem hướng dẫn\n"
        "- Khi đang thao tác, gõ /cancel để hủy"
        ,
        parse_mode="Markdown"
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/help - detailed guide (outside flow)."""
    await update.message.reply_text(
        "📖 *Hướng dẫn sử dụng*\n"
        "  1. Gõ /route để bắt đầu\n"
        "  2. Nhập điểm đi bằng chữ (ví dụ: tên địa điểm, số nhà,…)\n"
        "  3. Chọn điểm đi từ danh sách gợi ý\n"
        "  4. Nhập điểm đến và chọn điểm đến\n"
        "  5. Chọn phương tiện (hiện tại: Ô tô) và nhận kết quả\n\n"
        " *Ghi chú:*\n"
        "- ETA là thời gian ước tính dựa trên hệ thống định tuyến (OSRM)\n"
        "- Gõ /cancel để hủy thao tác bất kỳ lúc nào"
        ,
        parse_mode="Markdown"
    )



# =========================
# Entry point to flow
# =========================
async def route_entry(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """/route - start flow, ask FROM."""
    init_context(context.user_data)
    await update.message.reply_text(
        "Bắt đầu tìm đường.\n"
        "Bạn đi từ đâu? (Nhập địa điểm xuất phát bằng chữ)"
    )
    return FROM_TEXT

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """/cancel - cancel flow (fallback)."""
    init_context(context.user_data)
    await update.message.reply_text("Đã hủy. Gõ /route để bắt đầu lại.")
    return ConversationHandler.END

# =========================
# Services placeholders
# =========================
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



def format_result_message(
    from_label: str,
    to_label: str,
    distance_m: float,
    duration_s: float,
    link: str,
) -> str:
    """Format final result message."""
    # TODO: implement output template
    a = from_label.split("—")[0].strip()
    b = to_label.split("—")[0].strip()

    # Convert units
    distance_km = distance_m / 1000
    duration_min = round(duration_s / 60)

    return (
        f"✅ *Tuyến đường*\n"
        f"{a} → {b}\n\n"
        f"📐 *{distance_km:.1f} km*   ⏱️ *{duration_min} phút*\n"
        f"🗺️ [Mở chỉ đường trên OSM]({link})\n\n"
        f"🔁 Gõ /route để tìm tuyến khác hoặc /help"
    )

# =========================
# State handlers
# =========================
async def handle_from_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    FROM_TEXT:
    - receive text as from_text
    - call geocode_nominatim(from_text)
      - if 0 results: ask user to enter again, keep FROM_TEXT
      - if >=1: normalize_candidates -> save -> show inline keyboard -> FROM_PICK
    """
    # TODO: implement
    text = update.message.text.strip()

    # Save user input
    context.user_data["from_text"] = text

    # Call Nominatim (already limited to 3)
    raw_list = geocode_nominatim(text)

    # geocode = 0
    if not raw_list:
        context.user_data["from_candidates"] = []
        await update.message.reply_text(
            "Không tìm thấy địa điểm. "
            "Bạn nhập rõ hơn nhé (VD: tên địa điểm, số nhà, đường, phường, quận, TP.HCM)."
        )
        return FROM_TEXT
    
    # geocode >= 1
    candidates = normalize_candidates(raw_list)
    context.user_data["from_candidates"] = candidates

    # Show inline keyboard
    keyboard = [
        [InlineKeyboardButton(c["label"], callback_data=f"PICK_FROM_{i}")]
        for i, c in enumerate(candidates)
    ]
    keyboard.append([InlineKeyboardButton("Nhập lại", callback_data="BACK_FROM")])

    await update.message.reply_text(
        "Mình tìm thấy các địa điểm sau. Bạn chọn đúng điểm xuất phát:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )

    return FROM_PICK


async def handle_from_pick(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    FROM_PICK:
    - callback: PICK_FROM_i or BACK_FROM
    - set from_coord/from_label -> ask TO -> TO_TEXT
    """
    # TODO: implement
    q = update.callback_query
    await q.answer()

    data = q.data or ""

    if data == "BACK_FROM":
        clear_from(context.user_data)
        # Ẩn keyboard cũ + báo nhập lại ngay trên message đó
        await q.edit_message_text("↩️ Ok, bạn nhập lại điểm xuất phát nhé.")
        await q.message.reply_text(
            "Bạn đi từ đâu? (Nhập địa điểm xuất phát)"
        )
        return FROM_TEXT

    # data chắc chắn là PICK_FROM_i (do pattern)
    idx = int(data.split("_")[-1])
    chosen = context.user_data["from_candidates"][idx]

    context.user_data["from_coord"] = (chosen["lat"], chosen["lon"])
    context.user_data["from_label"] = chosen["label"]

    # 📍 collapse message chứa keyboard thành 1 dòng xác nhận
    await q.edit_message_text(f"📍 Đã chọn điểm xuất phát: {chosen['label']}")

    await q.message.reply_text(
        "Bạn muốn đến đâu? (Nhập địa điểm đích)"
    )
    return TO_TEXT

    

async def handle_to_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    TO_TEXT:
    - receive text as to_text
    - call geocode_nominatim(to_text)
      - if 0 results: ask user to enter again, keep TO_TEXT
      - if >=1: normalize_candidates -> save -> show inline keyboard -> TO_PICK
    """
    # TODO: implement
    text = update.message.text.strip()

    # Save user input
    context.user_data["to_text"] = text

    # Call Nominatim (already limited to 3)
    raw_list = geocode_nominatim(text)
    
    # geocode = 0
    if not raw_list:
        context.user_data["to_candidates"] = []
        await update.message.reply_text(
            "Không tìm thấy địa điểm. "
            "Bạn nhập rõ hơn nhé (VD: tên địa điểm, số nhà, đường, phường, quận, TP.HCM)."
        )
        return TO_TEXT

    # geocode >= 1
    candidates = normalize_candidates(raw_list)
    context.user_data["to_candidates"] = candidates

    # Show inline keyboard
    keyboard = [
        [InlineKeyboardButton(c["label"], callback_data=f"PICK_TO_{i}")]
        for i, c in enumerate(candidates)
    ]
    keyboard.append([InlineKeyboardButton("Nhập lại", callback_data="BACK_TO")])

    await update.message.reply_text(
        "Mình tìm thấy các địa điểm sau. Bạn chọn đúng điểm đến:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )
    return TO_PICK



async def handle_to_pick(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    TO_PICK:
    - callback: PICK_TO_i or BACK_TO
    - set to_coord/to_label -> show MODE keyboard -> MODE
    """
    # TODO: implement
    q = update.callback_query
    await q.answer()

    data = q.data

    if data == "BACK_TO":
        clear_to(context.user_data)
        await q.edit_message_text("↩️ Ok, bạn nhập lại điểm đến nhé.")
        await q.message.reply_text("Bạn muốn đến đâu? (Nhập địa điểm đến)")
        return TO_TEXT
    
    # data chắc chắn là PICK_TO_i (do pattern)
    idx = int(data.split("_")[-1])
    chosen = context.user_data["to_candidates"][idx]

    context.user_data["to_coord"] = (chosen["lat"], chosen["lon"])  # (lat, lon)
    context.user_data["to_label"] = chosen["label"]

    # 📍 collapse message chứa keyboard (ẩn nút)
    await q.edit_message_text(f"📍 Đã chọn điểm đến: {chosen['label']}")


    # MODE keyboard (demo: car only)
    keyboard = [
        [InlineKeyboardButton("🚗 Ô tô", callback_data="MODE_CAR"), InlineKeyboardButton("⏭️ Bỏ qua (mặc định Ô tô)", callback_data="MODE_SKIP")],
    ]

    await q.message.reply_text(
        "🚦 Chọn phương tiện (bản demo hiện chỉ hỗ trợ Ô tô):",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )
    return MODE



async def handle_mode(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    MODE:
    - callback: MODE_CAR or MODE_SKIP
    - set mode="car" (ONLY here)
    - call OSRM -> build OSM link -> reply result -> END
    """
    # TODO: implement
    q = update.callback_query
    await q.answer()

    data = q.data  # MODE_CAR or MODE_SKIP

    # Demo: both choices lead to car
    context.user_data["mode"] = "car"

    # Collapse the mode keyboard message
    if data == "MODE_CAR":
        await q.edit_message_text("Đã chọn phương tiện: 🚗")
    else:
        await q.edit_message_text("Bỏ qua chọn phương tiện (mặc định 🚗)")

    from_coord = context.user_data.get("from_coord")
    to_coord = context.user_data.get("to_coord")
    from_label = context.user_data.get("from_label") 
    to_label = context.user_data.get("to_label") 

    route = osrm_route(from_coord, to_coord)
    if not route:
        await q.message.reply_text(
            "Xin lỗi, mình không tính được lộ trình lúc này (OSRM lỗi/không có tuyến). "
            "Bạn thử lại với /route nhé."
        )
        return ConversationHandler.END
    
    distance_m = route["distance_m"]
    duration_s = route["duration_s"]

    link = build_osm_directions_link(from_coord, to_coord)

    context.user_data["route_result"] = {
        "distance_m": distance_m,
        "duration_s": duration_s,
        "link": link,
    }

    msg = format_result_message(from_label, to_label, distance_m, duration_s, link)
    await q.message.reply_text(
        msg, 
        parse_mode="Markdown",
        disable_web_page_preview=True,
    )

    return ConversationHandler.END

# =========================
# Extra handlers
# =========================
async def handle_non_text_from(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Mình chỉ nhận địa điểm dạng chữ. Bạn nhập điểm xuất phát bằng text nhé.")
    return FROM_TEXT

async def handle_non_text_to(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Mình chỉ nhận địa điểm dạng chữ. Bạn nhập điểm đến bằng text nhé.")
    return TO_TEXT

async def handle_text_in_from_pick(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Vui lòng bấm chọn một địa điểm bên dưới hoặc bấm ‘Nhập lại’.")
    return FROM_PICK

async def handle_text_in_to_pick(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Vui lòng bấm chọn một địa điểm bên dưới hoặc bấm ‘Nhập lại’.")
    return TO_PICK

async def handle_text_in_mode(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Vui lòng bấm chọn ‘Ô tô’ hoặc ‘Bỏ qua’.")
    return MODE

async def handle_invalid_callback_from_pick(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    q = update.callback_query
    await q.answer("Lựa chọn không hợp lệ", show_alert=False)
    await q.message.reply_text("Lựa chọn không hợp lệ. Bạn chọn lại trong danh sách bên trên nhé.")
    return FROM_PICK

async def handle_invalid_callback_to_pick(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    q = update.callback_query
    await q.answer("Lựa chọn không hợp lệ", show_alert=False)
    await q.message.reply_text("Lựa chọn không hợp lệ. Bạn chọn lại trong danh sách bên trên nhé.")
    return TO_PICK

async def handle_invalid_callback_mode(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    q = update.callback_query
    await q.answer("Lựa chọn không hợp lệ", show_alert=False)
    await q.message.reply_text("Lựa chọn không hợp lệ. Bạn chọn lại trong danh sách bên trên nhé.")
    return MODE

# =========================
# Build app
# =========================
def build_application() -> Application:
    application = Application.builder().token(TOKEN).build()

    # Global commands (outside flow)
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))

    # ConversationHandler (FSM)
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("route", route_entry)],
        states={
            FROM_TEXT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_from_text),
                MessageHandler(~filters.TEXT & ~filters.COMMAND, handle_non_text_from),
            ],
            FROM_PICK: [
                CallbackQueryHandler(handle_from_pick, pattern=r"^(PICK_FROM_\d+|BACK_FROM)$"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_in_from_pick),
                CallbackQueryHandler(handle_invalid_callback_from_pick, pattern=r"^.*$"),
            ],
            TO_TEXT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_to_text),
                MessageHandler(~filters.TEXT & ~filters.COMMAND, handle_non_text_to),
            ],
            TO_PICK: [
                CallbackQueryHandler(handle_to_pick, pattern=r"^(PICK_TO_\d+|BACK_TO)$"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_in_to_pick),
                CallbackQueryHandler(handle_invalid_callback_to_pick, pattern=r"^.*$"),
            ],
            MODE: [
                CallbackQueryHandler(handle_mode, pattern=r"^(MODE_CAR|MODE_SKIP)$"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_in_mode),
                CallbackQueryHandler(handle_invalid_callback_mode, pattern=r"^.*$"),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        allow_reentry=False,
    )

    application.add_handler(conv_handler)

    return application

def main() -> None:
    application = build_application()
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
