import argparse

from app.script_utils import run_search


def main():
    parser = argparse.ArgumentParser(
        description="Run a manual FAISS-backed transcript search using shared app logic."
    )
    parser.add_argument("query", nargs="?", help="Search query to run")
    parser.add_argument("--top-k", type=int, default=5)
    args = parser.parse_args()

    query = args.query or input("Enter a search query: ").strip()
    results = run_search(query, top_k=args.top_k)

    if not results:
        print("\nNo relevant chunks were found.")
        return

    print("\nTop results:\n")

    for rank, chunk in enumerate(results, start=1):
        print(f"Result {rank}")
        print(f"Chunk ID: {chunk['chunk_id']}")
        print(f"Video ID: {chunk['video_id']}")
        print(f"Start: {chunk['start']:.2f} | End: {chunk['end']:.2f}")
        print(f"Distance: {chunk['distance']:.4f}")
        print("Text preview:")
        print(chunk["text"][:300])
        print("-" * 60)


if __name__ == "__main__":
    main()
