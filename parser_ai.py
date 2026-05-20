"""
Parser Module - Uses OpenAI GPT-4o-mini to parse and rank listings
"""

import os
import json
import logging
import httpx
from openai import OpenAI

log = logging.getLogger(__name__)

# Fix SSL issues on local Windows
http_client = httpx.Client(verify=False)
client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

SYSTEM_PROMPT = """You are a real estate listing parser for Bangalore rentals.
Given raw listing text, extract structured data and return ONLY valid JSON.
No explanation, no markdown, just raw JSON array."""

USER_PROMPT_TEMPLATE = """
Parse these rental listings and return a JSON array. For each listing extract:
- id: unique identifier (from URL or title)
- title: BHK type and property type (e.g. "2BHK Apartment")
- price: monthly rent as integer (numbers only)
- deposit: security deposit as integer (0 if not mentioned)
- location: specific area in HSR Layout (e.g. "HSR Layout Sector 2")
- area_sqft: area in sqft as integer (0 if unknown)
- furnishing: one of "Fully Furnished", "Semi Furnished", "Unfurnished"
- amenities: list of key amenities mentioned (max 5)
- contact: phone number if visible, else ""
- url: listing URL
- score: your rating 1-10 based on value for money (10 = best deal under 30k)
- score_reason: one sentence why you gave this score

Listings to parse:
{listings_text}

Return ONLY a valid JSON array. No markdown.
"""


def parse_and_rank_listings(raw_listings: list[dict]) -> list[dict]:
    """
    Sends raw listings to OpenAI for parsing and ranking.
    Returns sorted list (best score first).
    """
    if not raw_listings:
        return []

    # Batch listings into groups of 10 to stay within token limits
    batch_size = 10
    all_parsed = []

    for i in range(0, len(raw_listings), batch_size):
        batch = raw_listings[i:i + batch_size]
        parsed = parse_batch(batch)
        all_parsed.extend(parsed)

    # Filter: only keep listings within budget
    filtered = [l for l in all_parsed if 0 < l.get("price", 99999) <= 30000]

    # Sort by score descending
    filtered.sort(key=lambda x: x.get("score", 0), reverse=True)

    return filtered


def parse_batch(batch: list[dict]) -> list[dict]:
    """Parses a single batch of listings via OpenAI."""
    # Build text input for the prompt
    listings_text = ""
    for idx, listing in enumerate(batch, 1):
        listings_text += f"\n--- Listing {idx} ---\n"
        listings_text += f"URL: {listing.get('url', 'N/A')}\n"
        listings_text += f"Raw text: {listing.get('raw_text', '')[:500]}\n"

    prompt = USER_PROMPT_TEMPLATE.format(listings_text=listings_text)

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=2000,
        )

        content = response.choices[0].message.content.strip()

        # Clean up any accidental markdown fences
        content = content.replace("```json", "").replace("```", "").strip()

        parsed = json.loads(content)

        if isinstance(parsed, list):
            return parsed
        elif isinstance(parsed, dict):
            return [parsed]
        else:
            log.warning("Unexpected OpenAI response format")
            return []

    except json.JSONDecodeError as e:
        log.error(f"JSON parse error from OpenAI response: {e}")
        return []
    except Exception as e:
        log.error(f"OpenAI API error: {e}")
        return []
