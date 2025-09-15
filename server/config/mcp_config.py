"""MCP configuration for Places server integration.

This module extends the existing MCP configuration to include the Places server,
allowing the ReAct agent to access place search functionality.
"""

import os
from typing import Any, Dict

# Get the project root directory
PROJECT_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)


def get_places_mcp_config() -> Dict[str, Dict[str, Any]]:
    """Get MCP server configuration for Places functionality.

    Returns:
        Dictionary containing Places MCP server configuration
    """
    return {
        "places": {
            "command": "python",
            "args": [os.path.join(PROJECT_ROOT, "server/mcp/places_mcp_server.py")],
            "transport": "stdio",
            "env": {
                # Environment variables for the places server
                "PYTHONPATH": PROJECT_ROOT,
                "TAVILY_API_KEY": os.getenv("TAVILY_API_KEY", ""),
                # Add other environment variables as needed
                "LOG_LEVEL": os.getenv("LOG_LEVEL", "INFO"),
            },
        }
    }


def extend_mcp_servers_config(
    existing_config: Dict[str, Dict[str, Any]],
) -> Dict[str, Dict[str, Any]]:
    """Extend existing MCP servers configuration with Places server.

    Args:
        existing_config: Current MCP servers configuration

    Returns:
        Extended configuration including Places server
    """
    places_config = get_places_mcp_config()

    # Merge with existing configuration
    extended_config = existing_config.copy()
    extended_config.update(places_config)

    return extended_config


# Configuration that can be imported and used to extend the main MCP_SERVERS
PLACES_MCP_SERVER_CONFIG = get_places_mcp_config()


def get_full_mcp_config_with_places() -> Dict[str, Dict[str, Any]]:
    """Get complete MCP configuration including Places server.

    This function imports the existing MCP configuration and extends it
    with the Places server configuration.

    Returns:
        Complete MCP configuration with Places server included
    """
    try:
        # Import the existing MCP configuration
        from src.common.mcp import MCP_SERVERS

        # Extend with Places configuration
        return extend_mcp_servers_config(MCP_SERVERS)

    except ImportError:
        # If can't import existing config, return just the Places config
        return PLACES_MCP_SERVER_CONFIG


# Example usage for testing
if __name__ == "__main__":
    import json
    import logging

    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    config = get_full_mcp_config_with_places()
    logger.info("Complete MCP Configuration with Places:")
    logger.info(json.dumps(config, indent=2))
