from pathlib import Path
import json
import numpy as np
import faiss


def normalize_faiss_vectors(vectors: np.ndarray) -> np.ndarray:
    normalized_vectors = np.array(vectors, dtype="float32", copy=True)

    if normalized_vectors.ndim != 2 or normalized_vectors.size == 0:
        return normalized_vectors

    # Unit-normalize vectors so inner product becomes cosine-similarity-equivalent
    faiss.normalize_L2(normalized_vectors)
    return normalized_vectors


# Build a FAISS index from embeddings
def build_faiss_index(embeddings: list[list[float]]):

    # Convert the list of embeddings into a NumPy array
    # FAISS requires vectors in NumPy format and specifically float32
    vectors = normalize_faiss_vectors(np.array(embeddings, dtype="float32"))

    # Get the dimension (size) of each embedding vector
    dimension = vectors.shape[1]

    # With normalized vectors, inner product ranking is equivalent to cosine similarity
    index = faiss.IndexFlatIP(dimension)

    # Add all embedding vectors into the FAISS index
    # Each vector becomes searchable
    index.add(vectors)

    # Return the built index so it can be used later
    return index


# Save the FAISS index to disk
def save_faiss_index(index, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)

    # write_index saves the binary FAISS index file
    # This allows us to reuse the index without rebuilding it
    faiss.write_index(index, str(path))


# Load a FAISS index from disk
def load_faiss_index(path: Path):

    # read_index loads a previously saved FAISS index
    # This restores the searchable vector database
    return faiss.read_index(str(path))


# Save the FAISS-to-chunk mapping to disk
def save_mapping(mapping: list[dict], path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)

    # Open the file in write mode with UTF-8 encoding
    with open(path, "w", encoding="utf-8") as f:

        # Save the mapping as JSON
        # indent=2 makes the file readable
        json.dump(mapping, f, indent=2)


# Load the FAISS to chunk mapping from disk
def load_mapping(path: Path):

    # Open the file in read mode
    with open(path, "r", encoding="utf-8") as f:

        # Load the JSON mapping and return it
        return json.load(f)


# Delete persisted FAISS files so the runtime can safely reload to an empty state
def delete_faiss_artifacts(*paths: Path):
    for path in paths:
        path.unlink(missing_ok=True)
