"""JSON parsing utilities with error handling

Provides type-safe JSON deserialization with consistent error handling,
logging, and Pydantic model validation.
"""

import json
from typing import Any, Dict, List, Optional, Type, TypeVar

from loguru import logger

T = TypeVar("T")


def parse_json_body(
    json_str: Optional[str],
    target_class: Type[T],
    field_name: str = "field",
    allow_list: bool = False,
) -> Optional[T]:
    """
    Parse a JSON string and deserialize to a Pydantic model instance.

    Handles:
    - None/empty string inputs
    - JSON parsing errors
    - Schema validation errors
    - Graceful fallback to None on any error

    Args:
        json_str: Raw JSON string from database
        target_class: Pydantic model class to deserialize into (e.g., BiasCompass)
        field_name: Human-readable field name for error logging
        allow_list: If True, accepts JSON arrays and returns list of instances

    Returns:
        Instance of target_class, or None if parsing/validation fails

    Examples:
        >>> bias = parse_json_body(event.bias_compass_json, BiasCompass, "bias_compass")
        >>> flags = parse_json_body(
        ...     article.fact_check_flags_json,
        ...     FactCheckFlag,
        ...     "fact_check_flags",
        ...     allow_list=True
        ... )
    """
    # Handle None/empty inputs
    if not json_str:
        return None

    if not isinstance(json_str, str) or not json_str.strip():
        return None

    try:
        # Parse JSON string
        data = json.loads(json_str)

        # Validate structure
        if data is None:
            logger.debug(f"Skipping null {field_name} data")
            return None

        # Handle list deserialization
        if allow_list:
            if not isinstance(data, list):
                logger.warning(
                    f"{field_name}: Expected list in JSON, got {type(data).__name__}"
                )
                return None

            instances = []
            for i, item in enumerate(data):
                try:
                    if isinstance(item, dict):
                        instances.append(target_class(**item))
                    else:
                        logger.warning(
                            f"{field_name}[{i}]: Expected dict, got {type(item).__name__}"
                        )
                except Exception as e:
                    logger.warning(f"{field_name}[{i}]: Failed to parse item: {e}")
                    continue

            return instances if instances else None

        # Handle single object deserialization
        if not isinstance(data, dict):
            logger.warning(
                f"{field_name}: Expected dict in JSON, got {type(data).__name__}"
            )
            return None

        return target_class(**data)

    except json.JSONDecodeError as e:
        logger.warning(
            f"{field_name}: Invalid JSON syntax: {e}. Preview: {json_str[:100]}"
        )
        return None
    except TypeError as e:
        # Pydantic validation error (missing required fields, wrong types)
        logger.warning(f"{field_name}: Schema validation failed: {e}")
        return None
    except Exception as e:
        logger.warning(f"{field_name}: Unexpected error during deserialization: {e}")
        return None


def parse_json_list(
    json_str: Optional[str],
    target_class: Type[T],
    field_name: str = "field",
) -> List[T]:
    """
    Parse a JSON string as a list and deserialize to Pydantic model instances.

    Convenience wrapper around parse_json_body with allow_list=True.

    Args:
        json_str: Raw JSON array string from database
        target_class: Pydantic model class for list items
        field_name: Human-readable field name for error logging

    Returns:
        List of target_class instances, or empty list if parsing fails

    Examples:
        >>> flags = parse_json_list(
        ...     article.fact_check_flags_json,
        ...     FactCheckFlag,
        ...     "fact_check_flags"
        ... )
        >>> print(len(flags))  # Could be 0 if parse failed
    """
    result = parse_json_body(
        json_str, target_class, field_name=field_name, allow_list=True
    )
    return result if result else []


def safe_json_loads(json_str: Optional[str], default: Any = None) -> Any:
    """
    Safely parse JSON string, returning default value on any error.

    No schema validation - just raw JSON parsing.

    Args:
        json_str: JSON string to parse
        default: Value to return if parsing fails

    Returns:
        Parsed JSON object, or default value

    Examples:
        >>> entities = safe_json_loads(article.entities_json, default=[])
        >>> languages = safe_json_loads(event.languages_json, default=[])
    """
    if not json_str or not isinstance(json_str, str) or not json_str.strip():
        return default

    try:
        return json.loads(json_str)
    except (json.JSONDecodeError, Exception) as e:
        logger.debug(f"Failed to parse JSON, returning default: {e}")
        return default
