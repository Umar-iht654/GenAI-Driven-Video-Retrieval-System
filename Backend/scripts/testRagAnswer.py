import argparse

from app.answerGenerator import generate_answer
from app.script_utils import run_search


def main():
    parser = argparse.ArgumentParser(
        description="Run a manual RAG answer flow using shared search logic."
    )
    parser.add_argument("query", nargs="?", help="Question to answer")
    parser.add_argument("--top-k", type=int, default=3)
    args = parser.parse_args()

    query = args.query or input("Enter a question: ").strip()

    # Retrieve top matching transcript chunks
    retrieved_chunks = run_search(query, top_k=args.top_k)

    if not retrieved_chunks:
        print("\nNo relevant chunks were found.")
        return

    # Generate final answer using retrieved chunks
    result = generate_answer(query, retrieved_chunks)

    print("\nGenerated Answer:\n")
    print(result["answer"])

    print("\nChunks Used:\n")
    for chunk in result["chunks_used"]:
        print(
            f"- {chunk['chunk_id']} "
            f"(Video: {chunk['video_id']}, "
            f"{chunk['start']:.2f}s to {chunk['end']:.2f}s)"
        )

    print("\nRetrieved Chunk Previews:\n")
    for chunk in retrieved_chunks:
        print(f"Chunk ID: {chunk['chunk_id']}")
        print(f"Distance: {chunk['distance']:.4f}")
        print(f"Text: {chunk['text'][:250]}")
        print("-" * 60)


if __name__ == "__main__":
    main()
