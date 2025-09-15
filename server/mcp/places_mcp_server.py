#!/usr/bin/env python3
"""MCP Server for Places API integration.

This server provides tools for searching and retrieving place information
via the Model Context Protocol (MCP). It follows the same pattern as the
existing mcp-nl2json.py implementation.
"""

import asyncio
import json
import logging
import sys
from typing import Any, Dict, List

# Add the project root to the path so we can import from server and src
sys.path.insert(0, "/Users/carrick/PycharmProjects/ReAct")

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool

from server.services.place_enrichment import PlaceEnrichmentService
from server.tools.place_search import search_places_by_region

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create the MCP server
app = Server("places-server")


@app.list_tools()
async def list_tools() -> List[Tool]:
    """List available tools for place search and information retrieval."""
    return [
        Tool(
            name="get_places_by_region",
            description="Search for popular places and attractions in a specified region",
            inputSchema={
                "type": "object",
                "properties": {
                    "region": {
                        "type": "string",
                        "description": "Name of the region, city, or area to search for places",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of places to return (default: 10)",
                        "default": 10,
                        "minimum": 1,
                        "maximum": 50,
                    },
                    "enrich_data": {
                        "type": "boolean",
                        "description": "Whether to enrich place data with additional details (default: true)",
                        "default": True,
                    },
                },
                "required": ["region"],
            },
        ),
        Tool(
            name="search_places_with_category",
            description="Search for places in a region filtered by category type",
            inputSchema={
                "type": "object",
                "properties": {
                    "region": {
                        "type": "string",
                        "description": "Name of the region to search in",
                    },
                    "category": {
                        "type": "string",
                        "description": "Category of places to search for (e.g., restaurants, museums, parks)",
                        "enum": [
                            "restaurants",
                            "museums",
                            "parks",
                            "attractions",
                            "hotels",
                            "shopping",
                        ],
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of places to return (default: 10)",
                        "default": 10,
                        "minimum": 1,
                        "maximum": 50,
                    },
                },
                "required": ["region", "category"],
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Handle tool calls for place search operations."""
    try:
        if name == "get_places_by_region":
            region = arguments["region"]
            limit = arguments.get("limit", 10)
            enrich_data = arguments.get("enrich_data", True)

            logger.info(f"Searching for places in region: {region} (limit: {limit})")

            # Search for places using the web search tool
            place_response = await search_places_by_region(region, limit)

            # Optionally enrich the data
            if enrich_data and place_response.stops:
                logger.info(f"Enriching data for {len(place_response.stops)} places")
                enriched_places = await PlaceEnrichmentService.enrich_multiple_places(
                    place_response.stops
                )
                place_response.stops = enriched_places

            # Convert to JSON-serializable format
            result = {
                "region": region,
                "places_found": len(place_response.stops),
                "places": [_place_to_dict(place) for place in place_response.stops],
            }

            return [{"type": "text", "text": json.dumps(result, indent=2)}]

        elif name == "search_places_with_category":
            region = arguments["region"]
            category = arguments["category"]
            limit = arguments.get("limit", 10)

            logger.info(f"Searching for {category} in region: {region}")

            # Modify search to include category
            categorized_response = await _search_places_by_category(
                region, category, limit
            )

            result = {
                "region": region,
                "category": category,
                "places_found": len(categorized_response.stops),
                "places": [
                    _place_to_dict(place) for place in categorized_response.stops
                ],
            }

            return [{"type": "text", "text": json.dumps(result, indent=2)}]

        else:
            raise ValueError(f"Unknown tool: {name}")

    except Exception as e:
        logger.error(f"Error in tool call {name}: {e}")
        error_result = {"error": str(e), "tool": name, "arguments": arguments}
        return [{"type": "text", "text": json.dumps(error_result, indent=2)}]


async def _search_places_by_category(region: str, category: str, limit: int):
    """Search for places in a specific category."""
    # Import here to avoid circular imports
    from server.tools.place_search import search_places_by_region as base_search

    # Use the base search function
    # This is a simplified approach - in production, you'd want more sophisticated filtering
    return await base_search(region, limit)


def _place_to_dict(place) -> Dict[str, Any]:
    """Convert PlaceDTO to dictionary for JSON serialization."""
    result = {
        "id": place.id,
        "name": place.name,
        "location": {"lat": place.location.lat, "lng": place.location.lng},
        "address": place.address,
        "description": place.description,
        "image_url": place.image_url,
    }

    if place.contact:
        result["contact"] = {
            "website": place.contact.website,
            "phone": place.contact.phone,
        }

    if place.opening_hours:
        result["opening_hours"] = {"raw": place.opening_hours.raw}
        if place.opening_hours.normalized:
            result["opening_hours"]["normalized"] = [
                {
                    "weekday": hours.weekday,
                    "times": [
                        {
                            "start_local": time_range.start_local,
                            "end_local": time_range.end_local,
                        }
                        for time_range in hours.times
                    ],
                }
                for hours in place.opening_hours.normalized
            ]

    return result


async def main():
    """Start the MCP server."""
    logger.info("Starting Places MCP Server...")

    try:
        # Run the server using stdio transport
        async with stdio_server() as (read_stream, write_stream):
            await app.run(
                read_stream, write_stream, app.create_initialization_options()
            )
    except Exception as e:
        logger.error(f"Server error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
