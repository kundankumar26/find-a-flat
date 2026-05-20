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

log = logging.getLogger(__name__)

# ─── Config ───────────────────────────────────────────────────────────────────
MAX_BUDGET   = 30000
MIN_BUDGET   = 5000
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

# NoBroker internal API endpoint
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

    for page_no in range(1, MAX_PAGES + 1):
        log.info(f"  Fetching page {page_no}/{MAX_PAGES}...")

        params = {
            "pageNo":           page_no,
            "searchParam":      HSR_LAYOUT_SEARCH_PARAM,
            "sharedAccomodation": 0,
            "orderBy":          "nbRank,desc",
            "radius":           2,
            "traffic":          "true",
            "travelTime":       30,
            "propertyType":     "rent",
            "rent":             f"{MIN_BUDGET},{MAX_BUDGET}",
            "buildingType":     "AP,IH",   # Apartment, Independent House
            "city":             CITY,
        }

        try:
            resp = session.get(NOBROKER_API, params=params, timeout=15)
            resp.raise_for_status()
            data = resp.json()
        except requests.exceptions.HTTPError as e:
            log.error(f"HTTP error on page {page_no}: {e}")
            break
        except requests.exceptions.RequestException as e:
            log.error(f"Request failed on page {page_no}: {e}")
            break
        except ValueError:
            log.error(f"Invalid JSON response on page {page_no}")
            break

        # NoBroker returns data under resp['data'] as a list of property objects
        page_data = data.get("data", [])

        if not page_data:
            log.info(f"  No more listings at page {page_no}. Stopping.")
            break

        normalized = [normalize_listing(p) for p in page_data]
        all_listings.extend(normalized)
        log.info(f"  Got {len(normalized)} listings (total so far: {len(all_listings)})")

        time.sleep(SLEEP_BETWEEN_PAGES)

    return all_listings


def normalize_listing(prop: dict) -> dict:
    """
    Normalizes a raw NoBroker API property object into our standard format.
    NoBroker API returns very rich data — we extract the most useful fields.
    """
    prop_id  = str(prop.get("propertyId") or prop.get("id") or "")
    city     = prop.get("city", "bangalore").lower()

    return {
        # Identity
        "id":          prop_id,
        "url":         f"https://www.nobroker.in/property/residential/rent/{city}/{prop_id}",

        # Core listing info
        "title":       f"{prop.get('bhk', '')} {prop.get('buildingType', 'Property')}".strip(),
        "price":       int(prop.get("rent", 0) or 0),
        "deposit":     int(prop.get("deposit", 0) or 0),
        "area_sqft":   int(prop.get("carpetArea", 0) or prop.get("builtArea", 0) or 0),
        "furnishing":  prop.get("furnishing", "N/A"),

        # Location
        "location_raw": prop.get("localityName", "HSR Layout"),
        "sector":       prop.get("localityName", ""),
        "latitude":     prop.get("latitude"),
        "longitude":    prop.get("longitude"),

        # Availability
        "available_from": prop.get("availableFrom", ""),
        "property_age":   prop.get("propertyAge", ""),

        # Amenities & features
        "amenities":    prop.get("amenities", []),
        "parking":      prop.get("parking", ""),
        "water_supply": prop.get("waterSupply", ""),
        "facing":       prop.get("facing", ""),
        "floor":        f"{prop.get('floorNo', '')} of {prop.get('totalFloor', '')}".strip(" of"),

        # Contact
        "owner_name":   prop.get("ownerName", ""),
        "phone":        prop.get("phoneNo", ""),

        # Raw text for AI (JSON dump of full object for rich parsing)
        "raw_text": json.dumps({
            "bhk":          prop.get("bhk"),
            "rent":         prop.get("rent"),
            "deposit":      prop.get("deposit"),
            "furnishing":   prop.get("furnishing"),
            "locality":     prop.get("localityName"),
            "area":         prop.get("carpetArea"),
            "amenities":    prop.get("amenities"),
            "buildingType": prop.get("buildingType"),
            "availableFrom":prop.get("availableFrom"),
            "parking":      prop.get("parking"),
            "facing":       prop.get("facing"),
        }),
    }
