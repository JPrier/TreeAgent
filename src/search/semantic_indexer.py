"""Simple semantic indexing of project files."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

from .file_loader import load_project_files, read_file


@dataclass
class SemanticIndex:
    """Mapping of file paths to embedding vectors."""

    embeddings: Dict[str, np.ndarray]
    vectorizer: TfidfVectorizer

    def update_file(self, path: str | Path) -> None:
        """Update ``embeddings`` for ``path`` in-place."""
        emb = get_file_embedding(path, self)
        self.embeddings[str(path)] = emb

    def rank(self, query: str, top_k: int = 5) -> list[tuple[str, float]]:
        """Return ``top_k`` files ranked by similarity to ``query``."""
        q_vec = self.vectorizer.transform([query]).toarray()[0]
        scores = {
            path: float(np.dot(vec, q_vec))
            for path, vec in self.embeddings.items()
        }
        return sorted(scores.items(), key=lambda x: x[1], reverse=True)[:top_k]


def build_semantic_index(base_dir: str | Path = ".") -> SemanticIndex:
    """Return a :class:`SemanticIndex` for all project files under ``base_dir``."""
    files = load_project_files(base_dir)
    texts = [read_file(p) for p in files]
    vectorizer = TfidfVectorizer()
    matrix = vectorizer.fit_transform(texts)
    embeddings = {
        str(path): matrix[idx].toarray()[0]
        for idx, path in enumerate(files)
    }
    return SemanticIndex(embeddings=embeddings, vectorizer=vectorizer)


def get_file_embedding(path: str | Path, index: SemanticIndex) -> np.ndarray:
    """Return the embedding vector for ``path`` using ``index``'s vectorizer."""
    text = read_file(path)
    return index.vectorizer.transform([text]).toarray()[0]


def update_file_embedding(path: str | Path, index: SemanticIndex) -> None:
    """Update ``index`` with the embedding for ``path``."""
    index.update_file(path)


def rank_files_by_query(query: str, index: SemanticIndex, top_k: int = 5) -> list[tuple[str, float]]:
    """Rank indexed files by semantic similarity to ``query``."""
    return index.rank(query, top_k=top_k)
