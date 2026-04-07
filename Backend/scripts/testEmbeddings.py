import argparse

from app.embeddingFactory import get_single_embedding_function


def main():
    parser = argparse.ArgumentParser(
        description="Smoke-test one embedding provider with a sample text."
    )
    parser.add_argument(
        "--provider",
        choices=["local", "openai"],
        default="local",
        help="Embedding provider to test",
    )
    parser.add_argument(
        "--text",
        default="Supervised learning uses labelled data to train a model.",
        help="Sample text to embed",
    )
    args = parser.parse_args()

    embedding_function = get_single_embedding_function(args.provider)
    embedding = embedding_function(args.text)

    print(args.provider.upper())
    print(f"Length: {len(embedding)}")
    print(f"First 10 values: {embedding[:10]}")


if __name__ == "__main__":
    main()
