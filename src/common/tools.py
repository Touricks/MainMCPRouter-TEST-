"""This module provides example tools for web scraping and search functionality.

It includes a basic Tavily search function (as an example)

These tools are intended as free examples to get started. For production use,
consider implementing more robust and specialized tools tailored to your needs.
"""

import logging
from typing import Any, Callable, List, Optional, cast

from langchain_tavily import TavilySearch
from langgraph.runtime import get_runtime

from common.context import Context
from common.mcp import (
    MCP_SERVERS,
    get_deepwiki_tools,
    get_nl2json_tools,
    get_postgres_tools,
)

logger = logging.getLogger(__name__)


async def web_search(query: str) -> Optional[dict[str, Any]]:
    """Search for general web results.

    This function performs a search using the Tavily search engine, which is designed
    to provide comprehensive, accurate, and trusted results. It's particularly useful
    for answering questions about current events.
    """
    runtime = get_runtime(Context)
    wrapped = TavilySearch(max_results=runtime.context.max_search_results)
    return cast(dict[str, Any], await wrapped.ainvoke({"query": query}))


async def get_mcp_server_info() -> dict[str, Any]:
    """Get information about configured MCP servers.

    This function returns details about the MCP servers configured in the codebase,
    including server count, names, and transport types. Use this when asked about
    MCP servers in the system configuration.
    """
    server_info: dict[str, Any] = {
        "total_servers": len(MCP_SERVERS),
        "server_names": list(MCP_SERVERS.keys()),
        "servers": {},
    }

    for name, config in MCP_SERVERS.items():
        transport = config.get("transport", "unknown")
        server_detail: dict[str, Any] = {"transport": transport}

        if "url" in config:
            server_detail["url"] = config["url"]
        if "command" in config:
            server_detail["command"] = config["command"]

        server_info["servers"][name] = server_detail

    return server_info


async def get_tools() -> List[Callable[..., Any]]:
    """Get all available tools based on configuration."""
    tools: List[Callable[..., Any]] = [web_search, get_mcp_server_info]

    runtime = get_runtime(Context)

    if runtime.context.enable_deepwiki:
        deepwiki_tools = await get_deepwiki_tools()
        tools.extend(deepwiki_tools)
        logger.info(f"Loaded {len(deepwiki_tools)} deepwiki tools")

    if runtime.context.enable_postgres:
        postgres_tools = await get_postgres_tools()
        tools.extend(postgres_tools)
        logger.info(f"Loaded {len(postgres_tools)} postgres tools")

    if runtime.context.enable_nl2json:
        nl2json_tools = await get_nl2json_tools()
        tools.extend(nl2json_tools)
        logger.info(f"Loaded {len(nl2json_tools)} nl2json tools")

    return tools
