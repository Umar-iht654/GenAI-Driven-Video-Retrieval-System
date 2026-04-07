from app.auto_ingest import FAISS_INDEX_PATH, FAISS_MAPPING_PATH, rebuild_faiss_index


def main():
    rebuilt = rebuild_faiss_index()

    if rebuilt:
        print(f"FAISS index saved to: {FAISS_INDEX_PATH}")
        print(f"Mapping file saved to: {FAISS_MAPPING_PATH}")
    else:
        print("No embedded chunks were found. FAISS files were cleared.")


if __name__ == "__main__":
    main()
