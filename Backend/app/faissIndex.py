from pathlib import Path
import json
import numpy as np
import faiss


# Build a FAISS index from embeddings
def build_faiss_index(embeddings: list[list[float]]):

    # Convert the list of embeddings into a NumPy array
    # FAISS requires vectors in NumPy format and specifically float32
    vectors = np.array(embeddings, dtype="float32")

    # Get the dimension (size) of each embedding vector
    dimension = vectors.shape[1]

    # Create a FAISS index using L2 distance (Euclidean distance)
    # IndexFlatL2 means: Flat = no compression, exact search. L2 = Euclidean distance metric
    # This is the simplest FAISS index type
    index = faiss.IndexFlatL2(dimension)

    # Add all embedding vectors into the FAISS index
    # Each vector becomes searchable
    index.add(vectors)

    # Return the built index so it can be used later
    return index


# Save the FAISS index to disk
def save_faiss_index(index, path: Path):

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