"""Natural Language to JSON conversion using Gemini API via MCP server."""

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict

from dotenv import load_dotenv
from jsonschema import ValidationError, validate  # type: ignore[import-untyped]
from langchain_google_genai import ChatGoogleGenerativeAI
from mcp.server.fastmcp import FastMCP

# Load .env file from project root (3 levels up from src/common/models/)
env_path = Path(__file__).parents[3] / ".env"
if env_path.exists():
    load_dotenv(env_path)

logger = logging.getLogger(__name__)

mcp = FastMCP("nl2json")


@mcp.tool()
def nl_to_json(text: str, schema: Dict[str, Any], prompt: str = "", strict: bool = True) -> Dict[str, Any]:
    """Convert natural language to JSON using Gemini API.

    Args:
        text: Natural language text to convert
        schema: JSON schema for the expected output structure
        prompt: Optional custom prompt to guide the conversion
        strict: Whether to validate the output against the schema

    Returns:
        Parsed JSON object matching the schema

    Raises:
        ValueError: If GOOGLE_API_KEY is not set or if strict validation fails
        Exception: If API call fails and strict=True
    """
    # Get API key from environment
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY environment variable not set")

    try:
        # Initialize Gemini model with JSON mode
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash",
            google_api_key=api_key,
            temperature=0.1,  # Lower temperature for more consistent JSON
        )

        # Use structured output with the provided schema
        structured_llm = llm.with_structured_output(schema)

        # Combine prompt and text for the query
        if prompt:
            query = f"{prompt}\n\nText: {text}"
        else:
            query = f"Convert the following text to JSON according to the provided schema:\n\n{text}"

        # Get structured response from Gemini
        result = structured_llm.invoke(query)

        # Convert result to dict if needed
        if hasattr(result, "model_dump"):
            data = result.model_dump()
        elif hasattr(result, "dict"):
            data = result.dict()
        elif isinstance(result, dict):
            data = result
        else:
            # Fallback: try to parse as JSON string
            data = json.loads(str(result))

        # Validate against schema if strict mode
        if strict:
            validate(instance=data, schema=schema)

        return data

    except ValidationError as e:
        error_msg = f"Schema validation failed: {e.message}"
        if strict:
            raise ValueError(error_msg)
        logger.warning(error_msg)
        return {}

    except Exception as e:
        error_msg = f"Error in nl_to_json: {str(e)}"
        if strict:
            raise Exception(error_msg)
        logger.warning(error_msg)
        return {}

if __name__ == "__main__":
    mcp.run()  # 默认即 stdio
