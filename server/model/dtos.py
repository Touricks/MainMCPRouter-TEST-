"""Data Transfer Objects (DTOs) for the Trip Planner API.

Based on the OpenAPI specification, these dataclasses represent the data structures
used for API communication, particularly for planned itineraries and place information.
"""

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class GeoPoint:
    """Geographic coordinates (latitude and longitude)."""

    lat: float
    lng: float


@dataclass
class ContactDTO:
    """Contact information for a place."""

    website: Optional[str] = None
    phone: Optional[str] = None


@dataclass
class TimeRange:
    """Time range with local start and end times."""

    start_local: str  # HH:mm format, e.g., "10:00"
    end_local: str  # HH:mm format, e.g., "18:00"


@dataclass
class DailyHours:
    """Opening hours for a specific day of the week."""

    weekday: str  # Day name, e.g., "MONDAY"
    times: List[TimeRange]


@dataclass
class OpeningHoursDTO:
    """Opening hours information for a place."""

    raw: str  # Original hours text from source (e.g., Google)
    normalized: Optional[List[DailyHours]] = None


@dataclass
class PlaceDTO:
    """Complete information about a place/location."""

    id: str  # UUID format
    name: str
    location: GeoPoint
    address: str
    contact: Optional[ContactDTO] = None
    image_url: Optional[str] = None
    description: Optional[str] = None
    opening_hours: Optional[OpeningHoursDTO] = None


@dataclass
class PlaceResponse:
    """Places information for a region."""

    stops: List[PlaceDTO]


@dataclass
class PlannedStop:
    """A planned stop within a day's itinerary."""

    order: int  # Order within the day (1, 2, 3...)
    place: PlaceDTO
    arrival_local: str  # Local time HH:mm format, e.g., "10:15"
    depart_local: str  # Local time HH:mm format, e.g., "11:30"
    stay_minutes: int  # Duration at location in minutes
    note: Optional[str] = None


@dataclass
class PlannedDay:
    """A complete day plan with ordered stops."""

    date: str  # Date in YYYY-MM-DD format, e.g., "2025-10-02"
    stops: List[PlannedStop]
