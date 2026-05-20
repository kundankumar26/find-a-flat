"""
Notifier Module - Sends messages via Telegram Bot
"""

import os
import logging
import requests

log = logging.getLogger(__name__)

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")

TELEGRAM_API = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"


def send_telegram_message(text: str) -> bool:
    """
    Sends a message to the configured Telegram chat.
    Returns True on success, False on failure.
    """
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        log.error("Telegram credentials not set. Check TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID env vars.")
        return False

    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "Markdown",
        "disable_web_page_preview": False,
    }

    try:
        resp = requests.post(TELEGRAM_API, json=payload, timeout=10)
        if resp.status_code == 200:
            log.info("Telegram message sent successfully")
            return True
        else:
            log.error(f"Telegram API error {resp.status_code}: {resp.text}")
            return False
    except Exception as e:
        log.error(f"Failed to send Telegram message: {e}")
        return False


def format_listing_message(listing: dict) -> str:
    """
    Formats a parsed listing into a readable Telegram message.
    """
    score = listing.get("score", "N/A")
    score_emoji = "🟢" if score >= 8 else "🟡" if score >= 6 else "🔴"

    price = listing.get("price", 0)
    deposit = listing.get("deposit", 0)
    area = listing.get("area_sqft", 0)
    amenities = listing.get("amenities", [])
    amenities_str = ", ".join(amenities[:4]) if amenities else "N/A"

    msg = f"""
🏠 *{listing.get("title", "Property")}*
📍 {listing.get("location", "HSR Layout")}

💰 Rent: ₹{price:,}/mo
🔑 Deposit: ₹{deposit:,}
📐 Area: {area} sq ft
🛋️ {listing.get("furnishing", "N/A")}
✨ Amenities: {amenities_str}

{score_emoji} *Score: {score}/10*
_{listing.get("score_reason", "")}_

🔗 [View Listing]({listing.get("url", "")})
{'─' * 28}"""

    return msg.strip()
