from app.embeddingFactory import get_single_embedding_function


def main():
    embedding_function = get_single_embedding_function("openai")
    embedding = embedding_function("Hello world")
    print(len(embedding))


if __name__ == "__main__":
    main()
