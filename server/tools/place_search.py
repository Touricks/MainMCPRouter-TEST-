"""Place search tool using web search for region-based place discovery."""

import logging
import re
import uuid
from typing import Any, Dict, Optional

from server.model.dtos import ContactDTO, GeoPoint, PlaceDTO, PlaceResponse
from src.common.tools import web_search

logger = logging.getLogger(__name__)


async def search_places_by_region(region: str, limit: int = 10) -> PlaceResponse:
    """Search for places in a given region using web search.

    Args:
        region: Name of the region/city to search for places
        limit: Maximum number of places to return

    Returns:
        PlaceResponse containing list of places found in the region
    """
    try:
        # Construct search query for popular places and attractions
        search_query = f"popular places attractions restaurants {region} travel guide"

        # Use existing web search tool
        search_results = await web_search(search_query)

        if not search_results or not search_results.get("results"):
            logger.warning(f"No search results found for region: {region}")
            return PlaceResponse(stops=[])

        # Extract and parse place information from search results
        places = []
        seen_names = set()  # Avoid duplicates

        for result in search_results["results"][
            : limit * 2
        ]:  # Get more results to filter
            if len(places) >= limit:
                break

            place = _extract_place_from_result(result, region)
            if place and place.name not in seen_names:
                places.append(place)
                seen_names.add(place.name)

        logger.info(f"Found {len(places)} places for region: {region}")
        return PlaceResponse(stops=places)

    except Exception as e:
        logger.error(f"Error searching places for region {region}: {e}")
        return PlaceResponse(stops=[])


def _extract_place_from_result(
    result: Dict[str, Any], region: str
) -> Optional[PlaceDTO]:
    """Extract place information from a single search result.

    Args:
        result: Individual search result from web search
        region: Original region searched for

    Returns:
        PlaceDTO if place information could be extracted, None otherwise
    """
    try:
        title = result.get("title", "")
        content = result.get("content", "")
        url = result.get("url", "")

        # Extract place name from title (remove common suffixes)
        place_name = _clean_place_name(title)
        if not place_name or len(place_name) < 3:
            return None

        # Generate mock coordinates (in a real implementation, use geocoding API)
        coordinates = _generate_mock_coordinates(region)

        # Extract address information
        address = _extract_address(content, region)

        # Extract contact information
        contact = _extract_contact_info(content, url)

        # Generate a UUID for the place
        place_id = str(uuid.uuid4())

        # Extract description
        description = _extract_description(content)

        return PlaceDTO(
            id=place_id,
            name=place_name,
            location=coordinates,
            address=address,
            contact=contact,
            image_url=None,  # Would need image search or specific API
            description=description,
            opening_hours=None,  # Would need structured data or specific API
        )

    except Exception as e:
        logger.error(f"Error extracting place from result: {e}")
        return None


def _clean_place_name(title: str) -> str:
    """Clean and extract place name from search result title."""
    # Remove common suffixes and prefixes
    cleaned = re.sub(r"\s*-\s*(TripAdvisor|Yelp|Google Maps|Wikipedia).*$", "", title)
    cleaned = re.sub(r"^\d+\.\s*", "", cleaned)  # Remove numbering
    cleaned = re.sub(r"\s*\|\s*.*$", "", cleaned)  # Remove everything after |
    cleaned = re.sub(
        r"\s*\(\s*\d+.*?\)\s*", "", cleaned
    )  # Remove ratings in parentheses

    # Limit length and strip
    return cleaned.strip()[:100]


def _generate_mock_coordinates(region: str) -> GeoPoint:
    """Generate mock coordinates based on region name.

    In a real implementation, this would use a geocoding service.
    """
    # Simple hash-based coordinate generation for demo purposes
    region_hash = hash(region.lower()) % 360

    # Generate coordinates within reasonable ranges
    lat = 40.0 + (region_hash % 40) - 20  # Roughly -20 to +20 from base
    lng = -74.0 + (region_hash % 80) - 40  # Roughly -40 to +40 from base

    return GeoPoint(lat=lat, lng=lng)


def _extract_address(content: str, region: str) -> str:
    """Extract address information from content."""
    # Look for address patterns
    address_patterns = [
        r"\d+\s+[A-Za-z\s]+(?:Street|St|Avenue|Ave|Road|Rd|Drive|Dr|Boulevard|Blvd)",
        r"[A-Za-z\s]+,\s*[A-Za-z\s]+\s+\d{5}",
    ]

    for pattern in address_patterns:
        match = re.search(pattern, content)
        if match:
            return match.group(0)

    # Fallback to region name
    return f"{region} Area"


def _extract_contact_info(content: str, url: str) -> Optional[ContactDTO]:
    """Extract contact information from content and URL."""
    # Extract phone number
    phone_pattern = r"\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}"
    phone_match = re.search(phone_pattern, content)
    phone = phone_match.group(0) if phone_match else None

    # Use URL as website if it's not a search engine
    website = None
    if url and not any(
        domain in url for domain in ["google.com", "bing.com", "yahoo.com"]
    ):
        website = url

    if phone or website:
        return ContactDTO(website=website, phone=phone)

    return None


def _extract_description(content: str) -> Optional[str]:
    """Extract a brief description from content."""
    if not content:
        return None

    # Take first sentence or up to 200 characters
    sentences = content.split(".")
    if sentences:
        description = sentences[0].strip()
        if len(description) > 200:
            description = description[:200] + "..."
        return description if len(description) > 20 else None

    return None
