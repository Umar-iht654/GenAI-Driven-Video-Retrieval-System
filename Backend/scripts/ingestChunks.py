import argparse

from app.script_utils import ingest_subtitle_chunks


def main():
    parser = argparse.ArgumentParser(
        description="Ingest a subtitle file into MongoDB chunks using shared app logic."
    )
    parser.add_argument("--video-id", help="Video id to resolve from Data/subtitles/<video_id>.vtt")
    parser.add_argument("--subtitle-path", help="Explicit path to a .vtt subtitle file")
    parser.add_argument("--max-duration", type=float, default=60.0)
    parser.add_argument("--max-words", type=int, default=150)
    parser.add_argument(
        "--skip-embeddings",
        action="store_true",
        help="Insert chunk text only without generating local embeddings or rebuilding FAISS.",
    )
    args = parser.parse_args()

    result = ingest_subtitle_chunks(
        video_id=args.video_id,
        subtitle_path=args.subtitle_path,
        max_duration=args.max_duration,
        max_words=args.max_words,
        include_local_embeddings=not args.skip_embeddings,
        rebuild_index=not args.skip_embeddings,
    )

    print(f"Subtitle file: {result['subtitle_path']}")
    print(f"Video ID: {result['video_id']}")
    print(f"Parsed segments: {len(result['segments'])}")
    print(f"Created chunks: {len(result['chunks'])}")
    print(f"Inserted documents: {len(result['documents'])}")


if __name__ == "__main__":
    main()
