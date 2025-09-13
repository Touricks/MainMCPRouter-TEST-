"""Google GenAI model integrations for ReAct agent."""

import os
from typing import Any, Optional

from langchain_google_genai import ChatGoogleGenerativeAI


def create_google_genai_model(
    model_name: str,
    api_key: Optional[str] = None,
    **kwargs: Any,
) -> ChatGoogleGenerativeAI:
    """Create a Google GenAI model with proper configuration.

    Args:
        model_name: The model name (e.g., 'gemini-2.5-pro', 'gemini-pro')
        api_key: Google API key (defaults to env var GOOGLE_API_KEY)
        **kwargs: Additional model parameters

    Returns:
        Configured ChatGoogleGenerativeAI instance
    """
    # Get API key from env if not provided
    if api_key is None:
        api_key = os.getenv("GOOGLE_API_KEY")

    # Create model configuration
    config = {"model": model_name, "google_api_key": api_key, **kwargs}

    return ChatGoogleGenerativeAI(**config)
