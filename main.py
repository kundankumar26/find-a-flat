"""
House Search Agent - Main Orchestrator
Runs every 4 hours via GitHub Actions scheduler
"""

import logging
from dotenv import load_dotenv
load_dotenv()  # loads .env file for local runs
from scraper import scrape_nobroker
from parser_ai import parse_and_rank_listings
from database import init_db, get_new_listings, mark_as_seen
from notifier import send_telegram_message, format_listing_message

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
log = logging.getLogger(__name__)


def run_agent():
    log.info("🚀 House Search Agent started")

    # Step 1: Init DB
    init_db()

    # Step 2: Scrape listings
    log.info("🔍 Scraping NoBroker for HSR Layout listings...")
    raw_listings = scrape_nobroker()
    log.info(f"   Found {len(raw_listings)} raw listings")

    if not raw_listings:
        log.warning("No listings found. Site may have blocked the scraper.")
        send_telegram_message("⚠️ House Agent: No listings found this run. Site may be blocking.")
        return

    # Step 3: Parse + rank via OpenAI
    log.info("🤖 Parsing and ranking listings with AI...")
    parsed_listings = parse_and_rank_listings(raw_listings)
    log.info(f"   Parsed {len(parsed_listings)} listings")

    # Step 4: Filter only new listings (not seen before)
    new_listings = get_new_listings(parsed_listings)
    log.info(f"   {len(new_listings)} new listings (not seen before)")

    if not new_listings:
        log.info("No new listings this run. All already notified.")
        return

    # Step 5: Send Telegram notifications
    log.info("📲 Sending Telegram notifications...")
    header = f"🏠 *{len(new_listings)} New Listings Found in HSR Layout!*\n{'─'*30}\n"
    send_telegram_message(header)

    for listing in new_listings:
        msg = format_listing_message(listing)
        send_telegram_message(msg)
        mark_as_seen(listing["id"])

    log.info("✅ Agent run complete!")


if __name__ == "__main__":
    run_agent()
