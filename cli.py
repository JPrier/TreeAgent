"""CLI entry point compatibility module.

This module provides compatibility for Windows installations where
entry points might resolve differently. It imports and re-exports
the main function from the actual CLI module.

This addresses the issue where Windows pip installations generate entry scripts
that import 'cli' instead of 'src.cli', causing ModuleNotFoundError.
"""

try:
    # Try to import from the src package structure (development/editable install)
    from src.cli import main
except ImportError:
    # Fallback for potential different package structures
    try:
        from .cli import main
    except ImportError:
        raise ImportError("Could not import CLI main function from either src.cli or .cli")

__all__ = ['main']