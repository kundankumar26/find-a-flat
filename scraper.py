"""
Scraper Module - Uses NoBroker's internal REST API directly
Much simpler, faster, and more reliable than Playwright scraping.
Approach sourced from: github.com/iamshreeram/nobroker-scraper
"""

import time
import requests
import logging
import base64
import json
import urllib3

log = logging.getLogger(__name__)

# ─── Config ───────────────────────────────────────────────────────────────────
MAX_BUDGET   = 33000
MIN_BUDGET   = 15000
CITY         = "bangalore"
MAX_PAGES    = 5       # Each page has ~20 listings → up to 100 listings per run
SLEEP_BETWEEN_PAGES = 1.5  # seconds, avoids rate-limiting

# HSR Layout coordinates (lat/lon) — used by NoBroker's API for location search
# searchParam is a base64-encoded JSON array of location objects
HSR_LAYOUT_SEARCH_PARAM = base64.b64encode(json.dumps([
    {
        "lat": 12.9081,
        "lon": 77.6476,
        "placeId": "ChIJKWoswT1dUjoRpZsTFwAS_zw",
        "placeName": "HSR Layout",
        "showMap": False,
        "city": "bangalore"
    }
]).encode()).decode()

NOBROKER_API = "https://www.nobroker.in/api/v3/multi/property/RENT/filter"

HEADERS = {
    "Content-Type": "application/json",
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:120.0) "
        "Gecko/20100101 Firefox/120.0"
    ),
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate, br",
    "Referer": "https://www.nobroker.in/",
    "Origin": "https://www.nobroker.in",
    "Connection": "keep-alive",
}


def scrape_nobroker() -> list[dict]:
    """
    Calls NoBroker's internal REST API for HSR Layout rentals under budget.
    Returns a list of normalized listing dicts.
    """
    all_listings = []
    session = requests.Session()
    session.headers.update(HEADERS)
    session.verify = False

    for page_no in range(1, MAX_PAGES + 1):
        log.info(f"  Fetching page {page_no}/{MAX_PAGES}...")

        params = {
            "pageNo":             page_no,
            "searchParam":        HSR_LAYOUT_SEARCH_PARAM,
            "sharedAccomodation": 0,
            "orderBy":            "nbRank,desc",
            "radius":             2,
            "traffic":            "true",
            "travelTime":         30,
            "propertyType":       "rent",
            "rent":               f"{MIN_BUDGET},{MAX_BUDGET}",
            "buildingType":       "AP,IH",
            "city":               CITY,
        }

        try:
            resp = session.get(NOBROKER_API, params=params, timeout=15)
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            log.error(f"Request failed on page {page_no}: {e}")
            break

        page_data = data.get("data", [])
        if not page_data:
            log.info(f"  No more listings at page {page_no}. Stopping.")
            break

        # Log first item keys so we can see the actual API field names
        if page_no == 1 and page_data:
            log.info(f"  API fields available: {list(page_data[0].keys())}")

        normalized = [normalize_listing(p) for p in page_data]
        all_listings.extend(normalized)
        log.info(f"  Got {len(normalized)} listings (total: {len(all_listings)})")
        time.sleep(SLEEP_BETWEEN_PAGES)

    return all_listings


def safe_int(val) -> int:
    """Safely convert any value to int, return 0 on failure."""
    try:
        return int(float(str(val).replace(",", "").strip()))
    except Exception:
        return 0


def normalize_listing(prop: dict) -> dict:
    prop_id = str(
        prop.get("propertyId") or
        prop.get("id") or
        prop.get("listingId") or ""
    )

    # Area — try every known NoBroker field name
    area = safe_int(
        prop.get("carpetArea") or
        prop.get("builtArea") or
        prop.get("superBuiltArea") or
        prop.get("area") or
        prop.get("plotArea") or
        prop.get("totalArea") or
        prop.get("floorArea") or 0
    )

    # BHK title
    bhk   = prop.get("bhk") or prop.get("bedroomCount") or prop.get("bedrooms") or ""
    btype = prop.get("buildingType") or prop.get("propertyType") or "Apartment"
    title = f"{bhk} BHK {btype}".strip()

    # Price
    price = safe_int(
        prop.get("rent") or prop.get("price") or prop.get("expectedRent") or 0
    )

    # Deposit
    deposit = safe_int(
        prop.get("deposit") or prop.get("securityDeposit") or 0
    )

    # Location
    location = (
        prop.get("localityName") or
        prop.get("locality") or
        prop.get("location") or
        prop.get("address") or
        "HSR Layout"
    )

    # Furnishing
    furnishing = (
        prop.get("furnishing") or
        prop.get("furnishingStatus") or
        prop.get("furnishingType") or
        "N/A"
    )

    # Amenities
    amenities = prop.get("amenities") or prop.get("amenitiesList") or []

    # Correct NoBroker listing URL format
    url = f"https://www.nobroker.in/property/residential/rent/bangalore/HSR-Layout?propertyId={prop_id}"

    return {
        "id":             prop_id,
        "url":            url,
        "title":          title,
        "price":          price,
        "deposit":        deposit,
        "area_sqft":      area,
        "furnishing":     furnishing,
        "location_raw":   location,
        "sector":         location,
        "amenities":      amenities,
        "parking":        prop.get("parking") or prop.get("parkingDetails") or "",
        "water_supply":   prop.get("waterSupply") or "",
        "facing":         prop.get("facing") or "",
        "floor":          str(prop.get("floorNo") or prop.get("floor") or ""),
        "total_floors":   str(prop.get("totalFloor") or prop.get("totalFloors") or ""),
        "available_from": prop.get("availableFrom") or prop.get("availabilityDate") or "",
        "owner_name":     prop.get("ownerName") or prop.get("name") or "",
        "phone":          prop.get("phoneNo") or prop.get("phone") or prop.get("contactNo") or "",
        # Full raw dump so AI can extract anything we missed
        "raw_text":       json.dumps(prop),
    }
