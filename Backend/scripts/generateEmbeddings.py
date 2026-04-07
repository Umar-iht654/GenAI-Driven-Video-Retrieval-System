from app.script_utils import generate_missing_embeddings


def main():
    updated_count = generate_missing_embeddings("local")
    print(f"Generated local embeddings for {updated_count} chunks.")


if __name__ == "__main__":
    main()
