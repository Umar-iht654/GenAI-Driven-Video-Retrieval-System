from __future__ import annotations

import threading
from pathlib import Path

import numpy as np

from app.faissIndex import load_faiss_index, load_mapping, normalize_faiss_vectors


class IndexManager:
    def __init__(self, index_path: Path, mapping_path: Path):
        self.index_path = index_path
        self.mapping_path = mapping_path
        self._lock = threading.RLock()
        self._index = None
        self._mapping: list[dict] = []

    def load(self) -> bool:
        return self.reload()

    def is_ready(self) -> bool:
        with self._lock:
            return self._index is not None and bool(self._mapping)

    def reload(self) -> bool:
        with self._lock:
            if not self.index_path.exists() or not self.mapping_path.exists():
                self._index = None
                self._mapping = []
                return False

            index = load_faiss_index(self.index_path)
            mapping = load_mapping(self.mapping_path)

            if index.ntotal != len(mapping):
                raise ValueError(
                    "FAISS index size does not match mapping length: "
                    f"{index.ntotal} != {len(mapping)}"
                )

            self._index = index
            self._mapping = mapping
            return True

    def search(self, query_embedding: list[float], k: int = 3) -> list[dict]:
        with self._lock:
            if self._index is None or not self._mapping or k <= 0:
                return []

            query_vector = normalize_faiss_vectors(
                np.array([query_embedding], dtype="float32")
            )
            safe_k = min(k, len(self._mapping))
            scores, indices = self._index.search(query_vector, safe_k)

            hits = []
            for rank, faiss_idx in enumerate(indices[0]):
                if faiss_idx < 0 or faiss_idx >= len(self._mapping):
                    continue

                mapping_entry = dict(self._mapping[faiss_idx])
                cosine_score = float(scores[0][rank])
                mapping_entry["score"] = cosine_score
                mapping_entry["distance"] = float(1.0 - cosine_score)
                mapping_entry["faiss_position"] = int(faiss_idx)
                hits.append(mapping_entry)

            return hits
