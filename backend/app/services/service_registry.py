"""Service registry for managing singleton instances

This module provides a centralized registry for singleton services to prevent
repeated instantiation of heavy services like embedding models, NLP models,
and bias analyzers.
"""

from typing import Dict, Any, Optional
from threading import Lock

# Thread-safe lock for concurrent access
_lock = Lock()

# Singleton instances storage
_instances: Dict[str, Any] = {}


def get_instance(service_name: str, factory_fn, *args, **kwargs) -> Any:
    """
    Get or create a singleton instance of a service.

    Thread-safe lazy initialization. If the service hasn't been initialized yet,
    factory_fn is called once and the result is cached.

    Args:
        service_name: Unique name for the service (e.g., "embedding_model")
        factory_fn: Callable that creates the service instance
        *args: Positional arguments to pass to factory_fn
        **kwargs: Keyword arguments to pass to factory_fn

    Returns:
        The cached or newly created service instance
    """
    if service_name not in _instances:
        with _lock:
            # Double-check pattern: verify again inside lock
            if service_name not in _instances:
                _instances[service_name] = factory_fn(*args, **kwargs)

    return _instances[service_name]


def clear_instance(service_name: str) -> None:
    """Clear a specific service instance from the registry.

    Useful for testing or runtime reconfiguration.

    Args:
        service_name: Name of the service to clear
    """
    with _lock:
        if service_name in _instances:
            del _instances[service_name]


def clear_all() -> None:
    """Clear all service instances from the registry.

    Useful for testing or shutting down the application.
    """
    with _lock:
        _instances.clear()


def get_bias_analyzer():
    """Get or create the BiasAnalyzer singleton.

    Returns:
        BiasAnalyzer instance
    """
    from app.services.bias import BiasAnalyzer

    return get_instance("bias_analyzer", BiasAnalyzer)


def get_embedding_model():
    """Get or create the SentenceTransformer embedding model singleton.

    Returns:
        SentenceTransformer instance
    """
    from app.config import settings
    from sentence_transformers import SentenceTransformer

    def create_model():
        print(f"Loading embedding model: {settings.embedding_model}")
        model = SentenceTransformer(settings.embedding_model)
        print("✅ Embedding model loaded")
        return model

    return get_instance("embedding_model", create_model)


def get_nlp_model():
    """Get or create the spaCy NLP model singleton.

    Returns:
        spaCy language model instance
    """
    import spacy

    def create_nlp():
        try:
            print("Loading spaCy model: en_core_web_sm")
            nlp = spacy.load("en_core_web_sm")
            print("✅ spaCy model loaded")
            return nlp
        except OSError:
            print("❌ spaCy model not found, downloading...")
            import subprocess

            subprocess.run(["python", "-m", "spacy", "download", "en_core_web_sm"])
            nlp = spacy.load("en_core_web_sm")
            print("✅ spaCy model loaded")
            return nlp

    return get_instance("nlp_model", create_nlp)


def get_fact_checker():
    """Get or create the FactChecker singleton.

    Returns:
        FactChecker instance or None if initialization fails
    """
    from app.services.fact_check import FactChecker

    def create_fact_checker():
        try:
            print("Loading FactChecker service")
            checker = FactChecker()
            print("✅ FactChecker loaded")
            return checker
        except Exception as e:
            print(f"⚠️  Warning: Could not load FactChecker: {e}")
            return None

    return get_instance("fact_checker", create_fact_checker)
