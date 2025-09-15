#!/usr/bin/env python3
"""Test examples for Places functionality.

This script demonstrates how to use the Places search functionality
both directly and through the MCP server.
"""

import asyncio
import json
import logging
import sys

# Add the project root to the path
sys.path.insert(0, "/Users/carrick/PycharmProjects/ReAct")

from server.agent_extension import search_places_by_region_tool
from server.services.place_enrichment import PlaceEnrichmentService
from server.tools.place_search import search_places_by_region

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def test_direct_place_search():
    """Test direct place search functionality."""
    logger.info("=" * 60)
    logger.info("Testing Direct Place Search")
    logger.info("=" * 60)

    regions_to_test = ["Tokyo", "Paris", "New York"]  # Reduced for cleaner output

    for region in regions_to_test:
        try:
            logger.info(f"🔍 Searching for places in: {region}")

            # Search for places
            place_response = await search_places_by_region(region, limit=3)

            logger.info(f"Found {len(place_response.stops)} places:")

            for i, place in enumerate(place_response.stops, 1):
                logger.info(f"{i}. {place.name} at {place.address}")
                if place.description:
                    logger.info(f"   Description: {place.description[:80]}...")

        except Exception as e:
            logger.error(f"Error searching for places in {region}: {e}")


async def test_enriched_place_search():
    """Test place search with data enrichment."""
    logger.info("=" * 60)
    logger.info("Testing Enriched Place Search")
    logger.info("=" * 60)

    region = "San Francisco"

    try:
        logger.info(f"🔍 Searching for places in: {region} (with enrichment)")

        # Search for places
        place_response = await search_places_by_region(region, limit=2)

        if place_response.stops:
            logger.info(f"Found {len(place_response.stops)} places to enrich")

            # Enrich the data
            enriched_places = await PlaceEnrichmentService.enrich_multiple_places(
                place_response.stops
            )

            logger.info("📈 Enriched place data:")

            for i, place in enumerate(enriched_places, 1):
                logger.info(f"{i}. {place.name}")
                logger.info(f"   Address: {place.address}")

                if place.description:
                    logger.info(f"   Description: {place.description[:100]}...")

                if place.opening_hours:
                    logger.info(f"   Hours: {place.opening_hours.raw}")

    except Exception as e:
        logger.error(f"Error in enriched search: {e}")


async def test_agent_tool_format():
    """Test the agent-compatible tool format."""
    logger.info("=" * 60)
    logger.info("Testing Agent Tool Format")
    logger.info("=" * 60)

    region = "Barcelona"

    try:
        logger.info(f"🤖 Testing agent tool for: {region}")

        # Use the agent-compatible tool
        result = await search_places_by_region_tool(region, limit=2)

        # Display formatted result
        logger.info(f"Region: {result['region']}")
        logger.info(f"Places found: {result['places_found']}")

        if result.get("error"):
            logger.error(f"Error: {result['error']}")
        else:
            logger.info("Places found:")
            for place in result["places"]:
                logger.info(f"  • {place['name']} at {place['address']}")

    except Exception as e:
        logger.error(f"Error testing agent tool for {region}: {e}")


async def test_json_output():
    """Test JSON output format for API compatibility."""
    logger.info("=" * 60)
    logger.info("Testing JSON Output Format")
    logger.info("=" * 60)

    region = "Rome"

    try:
        logger.info(f"📄 Generating JSON output for: {region}")

        # Get agent tool result
        result = await search_places_by_region_tool(region, limit=2)

        # Convert to JSON and display
        json_output = json.dumps(result, indent=2, ensure_ascii=False)
        logger.info("JSON Output generated successfully")

        # Validate JSON can be parsed
        parsed = json.loads(json_output)
        logger.info("✅ JSON validation successful")
        logger.info(f"   - Region: {parsed['region']}")
        logger.info(f"   - Places: {parsed['places_found']}")

    except Exception as e:
        logger.error(f"Error generating JSON output: {e}")


async def run_performance_test():
    """Run a simple performance test."""
    logger.info("=" * 60)
    logger.info("Performance Test")
    logger.info("=" * 60)

    regions = ["Berlin", "Stockholm"]  # Reduced for testing

    logger.info(f"⏱️ Testing search performance for {len(regions)} regions...")

    import time

    start_time = time.time()

    tasks = []
    for region in regions:
        task = search_places_by_region_tool(region, limit=2)
        tasks.append(task)

    try:
        results = await asyncio.gather(*tasks, return_exceptions=True)

        end_time = time.time()
        duration = end_time - start_time

        logger.info("📊 Performance Results:")
        logger.info(f"   - Total time: {duration:.2f} seconds")
        logger.info(f"   - Average per region: {duration / len(regions):.2f} seconds")

        successful_results = [r for r in results if not isinstance(r, Exception)]
        logger.info(
            f"   - Successful searches: {len(successful_results)}/{len(regions)}"
        )

        total_places = sum(r.get("places_found", 0) for r in successful_results)
        logger.info(f"   - Total places found: {total_places}")

    except Exception as e:
        logger.error(f"Performance test error: {e}")


async def main():
    """Run all test examples."""
    logger.info("🚀 Starting Places Functionality Tests")
    logger.info("=" * 80)

    try:
        # Run all tests
        await test_direct_place_search()
        await test_enriched_place_search()
        await test_agent_tool_format()
        await test_json_output()
        await run_performance_test()

        logger.info("=" * 80)
        logger.info("✅ All tests completed!")
        logger.info("=" * 80)

    except Exception as e:
        logger.error(f"Test suite error: {e}")
        logger.exception("Full test suite error details")


if __name__ == "__main__":
    asyncio.run(main())
