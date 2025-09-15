"""Service for enriching place data with additional information."""

import logging
from typing import List, Optional

from server.model.dtos import (
    ContactDTO,
    DailyHours,
    OpeningHoursDTO,
    PlaceDTO,
    TimeRange,
)
from src.common.tools import web_search

logger = logging.getLogger(__name__)


class PlaceEnrichmentService:
    """Service to enrich place data with additional details."""

    @staticmethod
    async def enrich_place_data(place: PlaceDTO) -> PlaceDTO:
        """Enrich a single place with additional information.

        Args:
            place: Basic place information to enrich

        Returns:
            Enhanced PlaceDTO with additional details
        """
        try:
            # Search for more detailed information about the place
            search_query = f"{place.name} hours contact information address"
            search_results = await web_search(search_query)

            enhanced_place = place

            if search_results and search_results.get("results"):
                # Try to enhance various fields
                enhanced_place = (
                    await PlaceEnrichmentService._enhance_from_search_results(
                        place, search_results["results"]
                    )
                )

            # Add default opening hours if none found
            if not enhanced_place.opening_hours:
                enhanced_place.opening_hours = (
                    PlaceEnrichmentService._generate_default_hours()
                )

            logger.info(f"Enriched place data for: {place.name}")
            return enhanced_place

        except Exception as e:
            logger.error(f"Error enriching place {place.name}: {e}")
            return place

    @staticmethod
    async def enrich_multiple_places(places: List[PlaceDTO]) -> List[PlaceDTO]:
        """Enrich multiple places with additional information.

        Args:
            places: List of places to enrich

        Returns:
            List of enriched PlaceDTO objects
        """
        enriched_places = []

        for place in places:
            enriched_place = await PlaceEnrichmentService.enrich_place_data(place)
            enriched_places.append(enriched_place)

        return enriched_places

    @staticmethod
    async def _enhance_from_search_results(
        place: PlaceDTO, results: List[dict]
    ) -> PlaceDTO:
        """Enhance place data from search results."""
        enhanced_contact = place.contact
        enhanced_description = place.description
        enhanced_hours = place.opening_hours

        for result in results[:3]:  # Check first 3 results
            content = result.get("content", "")

            # Enhance contact information
            if not enhanced_contact or not enhanced_contact.phone:
                phone = PlaceEnrichmentService._extract_phone(content)
                if phone:
                    website = enhanced_contact.website if enhanced_contact else None
                    enhanced_contact = ContactDTO(
                        website=website or result.get("url"), phone=phone
                    )

            # Enhance description if too short or missing
            if not enhanced_description or len(enhanced_description) < 50:
                description = PlaceEnrichmentService._extract_description(content)
                if description and len(description) > len(enhanced_description or ""):
                    enhanced_description = description

            # Try to extract opening hours
            if not enhanced_hours:
                hours = PlaceEnrichmentService._extract_opening_hours(content)
                if hours:
                    enhanced_hours = hours

        # Create new PlaceDTO with enhanced data
        return PlaceDTO(
            id=place.id,
            name=place.name,
            location=place.location,
            address=place.address,
            contact=enhanced_contact,
            image_url=place.image_url,
            description=enhanced_description,
            opening_hours=enhanced_hours,
        )

    @staticmethod
    def _extract_phone(content: str) -> Optional[str]:
        """Extract phone number from content."""
        import re

        # Phone number patterns
        patterns = [
            r"\(\d{3}\)\s*\d{3}-\d{4}",  # (555) 123-4567
            r"\d{3}-\d{3}-\d{4}",  # 555-123-4567
            r"\d{3}\.\d{3}\.\d{4}",  # 555.123.4567
            r"\+1\s*\d{3}\s*\d{3}\s*\d{4}",  # +1 555 123 4567
        ]

        for pattern in patterns:
            match = re.search(pattern, content)
            if match:
                return match.group(0)

        return None

    @staticmethod
    def _extract_description(content: str) -> Optional[str]:
        """Extract a good description from content."""
        if not content:
            return None

        # Split into sentences and find the best one
        sentences = content.split(".")

        for sentence in sentences:
            sentence = sentence.strip()
            # Look for descriptive sentences (not too short, not URLs, etc.)
            if (
                20 <= len(sentence) <= 300
                and not sentence.startswith("http")
                and not sentence.isdigit()
            ):
                return sentence + "."

        return None

    @staticmethod
    def _extract_opening_hours(content: str) -> Optional[OpeningHoursDTO]:
        """Extract opening hours from content."""
        import re

        # Look for hour patterns
        hour_patterns = [
            r"(Mon|Tue|Wed|Thu|Fri|Sat|Sun)[a-z]*:?\s*(\d{1,2}:\d{2}\s*[AP]M|\d{1,2}[AP]M)",
            r"Open\s*:?\s*(\d{1,2}:\d{2}\s*[AP]M|\d{1,2}[AP]M)",
            r"Hours?\s*:?\s*(\d{1,2}:\d{2}\s*[AP]M|\d{1,2}[AP]M)",
        ]

        for pattern in hour_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                raw_hours = match.group(0)
                return OpeningHoursDTO(
                    raw=raw_hours,
                    normalized=None,  # Would need more complex parsing
                )

        return None

    @staticmethod
    def _generate_default_hours() -> OpeningHoursDTO:
        """Generate default opening hours for places."""
        # Common business hours
        weekday_hours = TimeRange(start_local="09:00", end_local="18:00")
        weekend_hours = TimeRange(start_local="10:00", end_local="17:00")

        daily_hours = [
            DailyHours(weekday="MONDAY", times=[weekday_hours]),
            DailyHours(weekday="TUESDAY", times=[weekday_hours]),
            DailyHours(weekday="WEDNESDAY", times=[weekday_hours]),
            DailyHours(weekday="THURSDAY", times=[weekday_hours]),
            DailyHours(weekday="FRIDAY", times=[weekday_hours]),
            DailyHours(weekday="SATURDAY", times=[weekend_hours]),
            DailyHours(weekday="SUNDAY", times=[weekend_hours]),
        ]

        return OpeningHoursDTO(
            raw="Mon-Fri 9AM-6PM, Sat-Sun 10AM-5PM", normalized=daily_hours
        )
