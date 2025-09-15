"""Agent extension module for integrating Places functionality with ReAct agent.

This module provides functions to extend the existing ReAct agent with
place search capabilities, allowing the agent to respond to queries about
places and regions.
"""

import logging
from typing import Any, Callable, List

from server.tools.place_search import search_places_by_region
from src.common.context import Context
from src.common.mcp import get_mcp_tools

logger = logging.getLogger(__name__)


async def get_places_tools() -> List[Callable[..., Any]]:
    """Get place-related tools for the agent.

    This function loads MCP tools from the Places server if available,
    or falls back to direct tool functions.

    Returns:
        List of place-related tools that can be used by the agent
    """
    tools: List[Callable[..., Any]] = []

    try:
        # Try to get MCP tools from Places server
        places_mcp_tools = await get_mcp_tools("places")
        if places_mcp_tools:
            tools.extend(places_mcp_tools)
            logger.info(f"Loaded {len(places_mcp_tools)} MCP tools from Places server")
        else:
            # Fallback to direct tool functions
            tools.append(search_places_by_region_tool)
            logger.info("Using direct place search tools (MCP not available)")

    except Exception as e:
        logger.warning(f"Failed to load MCP Places tools: {e}")
        # Fallback to direct tool functions
        tools.append(search_places_by_region_tool)
        logger.info("Using direct place search tools as fallback")

    return tools


async def search_places_by_region_tool(region: str, limit: int = 10) -> dict:
    """Direct tool function for searching places by region.

    This is a wrapper around the search_places_by_region function that
    returns data in a format suitable for the ReAct agent.

    Args:
        region: Name of the region to search for places
        limit: Maximum number of places to return

    Returns:
        Dictionary containing place search results
    """
    try:
        place_response = await search_places_by_region(region, limit)

        # Convert to agent-friendly format
        result = {
            "region": region,
            "places_found": len(place_response.stops),
            "places": [],
        }

        for place in place_response.stops:
            place_dict = {
                "id": place.id,
                "name": place.name,
                "location": {
                    "latitude": place.location.lat,
                    "longitude": place.location.lng,
                },
                "address": place.address,
                "description": place.description,
            }

            if place.contact:
                place_dict["contact"] = {
                    "website": place.contact.website,
                    "phone": place.contact.phone,
                }

            if place.opening_hours:
                place_dict["opening_hours"] = place.opening_hours.raw

            result["places"].append(place_dict)

        logger.info(f"Found {len(place_response.stops)} places for region: {region}")
        return result

    except Exception as e:
        logger.error(f"Error searching places for region {region}: {e}")
        return {"region": region, "places_found": 0, "places": [], "error": str(e)}


def extend_agent_context(context: Context, enable_places: bool = True) -> Context:
    """Extend agent context to include Places functionality.

    Args:
        context: Existing agent context
        enable_places: Whether to enable Places tools

    Returns:
        Extended context with Places configuration
    """
    # Note: This would require modifying the Context dataclass to include
    # a places-specific flag. For now, we'll use existing flags or create
    # a custom approach.

    # In a real implementation, you might add:
    # context.enable_places = enable_places

    return context


async def register_places_with_agent():
    """Register Places functionality with the main ReAct agent.

    This function demonstrates how to integrate the Places tools
    with the existing agent infrastructure.
    """
    try:
        # Get Places tools
        places_tools = await get_places_tools()

        # In a real implementation, you would modify the get_tools function
        # in src/common/tools.py to include these tools based on configuration

        logger.info(
            f"Successfully registered {len(places_tools)} Places tools with agent"
        )
        return places_tools

    except Exception as e:
        logger.error(f"Failed to register Places tools with agent: {e}")
        return []


# Example of how to modify the existing tools.py get_tools function
async def enhanced_get_tools() -> List[Callable[..., Any]]:
    """Enhanced version of get_tools that includes Places functionality.

    This function shows how to extend the existing get_tools function
    to include Places tools based on configuration.

    Returns:
        List of all available tools including Places tools
    """
    # Import the original get_tools function
    from src.common.tools import get_tools as original_get_tools

    # Get original tools
    tools = await original_get_tools()

    # Add Places tools if enabled
    # Note: In a real implementation, you'd check a configuration flag
    enable_places = True  # This would come from context or environment

    if enable_places:
        places_tools = await get_places_tools()
        tools.extend(places_tools)
        logger.info(f"Added {len(places_tools)} Places tools to agent")

    return tools


# Usage example for demonstration
if __name__ == "__main__":
    import asyncio

    async def demo():
        """Demonstrate Places integration."""
        logger.info("Demonstrating Places integration with ReAct agent...")

        # Get Places tools
        tools = await get_places_tools()
        logger.info(f"Loaded {len(tools)} Places tools")

        # Test direct tool function
        result = await search_places_by_region_tool("Tokyo", limit=5)
        logger.info(f"Found {result['places_found']} places in Tokyo")

        # Register with agent
        await register_places_with_agent()
        logger.info("Places tools registered with agent")

    asyncio.run(demo())
