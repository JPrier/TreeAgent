"""Utilities for indexing and searching project files."""

from .file_loader import load_project_files, read_file
from .semantic_indexer import (
    SemanticIndex,
    build_semantic_index,
    get_file_embedding,
    update_file_embedding,
    rank_files_by_query,
)

__all__ = [
    "load_project_files",
    "read_file",
    "SemanticIndex",
    "build_semantic_index",
    "get_file_embedding",
    "update_file_embedding",
    "rank_files_by_query",
]
