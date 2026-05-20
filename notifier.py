"""
Notifier Module - Sends messages via Telegram Bot
"""

import os
import logging
import requests

log = logging.getLogger(__name__)

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID   = os.environ.get("TELEGRAM_CHAT_ID", "")
TELEGRAM_API = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"


def send_telegram_message(text: str) -> bool:
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        log.error("Telegram credentials not set.")
        return False

    payload = {
        "chat_id":                  TELEGRAM_CHAT_ID,
        "text":                     text,
        "parse_mode":               "Markdown",
        "disable_web_page_preview": True,
    }

    try:
        resp = requests.post(TELEGRAM_API, json=payload, timeout=10, verify=False)
        if resp.status_code == 200:
            return True
        else:
            log.error(f"Telegram error {resp.status_code}: {resp.text}")
            return False
    except Exception as e:
        log.error(f"Telegram send failed: {e}")
        return False


def format_listing_message(listing: dict) -> str:
    score        = listing.get("score", 0)
    score_emoji  = "🟢" if score >= 8 else "🟡" if score >= 6 else "🔴"

    price        = listing.get("price", 0)
    deposit      = listing.get("deposit", 0)
    area         = listing.get("area_sqft", 0)
    area_str     = f"{area} sq ft" if area and area > 0 else "Area N/A"

    floor        = listing.get("floor", "")
    total_floors = listing.get("total_floors", "")
    floor_str    = f"Floor {floor}/{total_floors}" if floor and total_floors else (f"Floor {floor}" if floor else "")

    amenities    = listing.get("amenities", [])
    if isinstance(amenities, list):
        amenities_str = ", ".join(amenities[:4]) if amenities else "N/A"
    else:
        amenities_str = str(amenities) or "N/A"

    available    = listing.get("available_from", "")
    available_str = f"\n🗓️ Available: {available}" if available else ""

    phone        = listing.get("phone", "")
    phone_str    = f"\n📞 {phone}" if phone else ""

    floor_line   = f"\n🏢 {floor_str}" if floor_str else ""

    msg = f"""🏠 *{listing.get("title", "Property")}*
📍 {listing.get("location_raw", "HSR Layout")}

💰 Rent: ₹{price:,}/mo
🔑 Deposit: ₹{deposit:,}
📐 {area_str}
🛋️ {listing.get("furnishing", "N/A")}{floor_line}
✨ {amenities_str}{available_str}{phone_str}

{score_emoji} *Score: {score}/10*
_{listing.get("score_reason", "")}_

🔗 [View Listing]({listing.get("url", "")})
{'─' * 28}"""

    return msg.strip()
