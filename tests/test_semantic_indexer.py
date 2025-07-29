from search.semantic_indexer import (
    build_semantic_index,
    get_file_embedding,
    update_file_embedding,
    rank_files_by_query,
)
import numpy as np


def test_build_semantic_index(tmp_path):
    (tmp_path / "a.txt").write_text("hello world")
    (tmp_path / "b.py").write_text("print('hi')")
    index = build_semantic_index(tmp_path)
    assert set(index.embeddings.keys()) == {
        str(tmp_path / "a.txt"),
        str(tmp_path / "b.py"),
    }
    for emb in index.embeddings.values():
        assert isinstance(emb, np.ndarray)
        assert emb.ndim == 1


def test_get_file_embedding(tmp_path):
    (tmp_path / "a.txt").write_text("hello")
    index = build_semantic_index(tmp_path)
    emb1 = get_file_embedding(tmp_path / "a.txt", index)
    emb2 = get_file_embedding(tmp_path / "a.txt", index)
    assert np.allclose(emb1, emb2)


def test_update_and_rank(tmp_path):
    f1 = tmp_path / "hello.txt"
    f2 = tmp_path / "bye.txt"
    f1.write_text("hello world")
    f2.write_text("goodbye world")
    index = build_semantic_index(tmp_path)

    # modify a file and update embedding
    f1.write_text("hello there")
    update_file_embedding(f1, index)

    ranking = rank_files_by_query("hello", index, top_k=2)
    assert ranking[0][0] == str(f1)
