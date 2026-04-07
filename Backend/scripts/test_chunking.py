import argparse

from app.script_utils import chunk_subtitle


def main():
    parser = argparse.ArgumentParser(
        description="Inspect chunking output for a subtitle file using shared app logic."
    )
    parser.add_argument("--video-id", help="Video id to resolve from Data/subtitles/<video_id>.vtt")
    parser.add_argument("--subtitle-path", help="Explicit path to a .vtt subtitle file")
    parser.add_argument("--max-duration", type=float, default=60.0)
    parser.add_argument("--max-words", type=int, default=150)
    args = parser.parse_args()

    result = chunk_subtitle(
        video_id=args.video_id,
        subtitle_path=args.subtitle_path,
        max_duration=args.max_duration,
        max_words=args.max_words,
    )

    print(f"Subtitle file: {result['subtitle_path']}")
    print(f"Video ID: {result['video_id']}")
    print(f"Parsed subtitle segments: {len(result['segments'])}")
    print(f"Created chunks: {len(result['chunks'])}")
    print()

    for chunk in result["chunks"][:3]:
        print(f"{chunk.chunk_id}")
        print(f"Start: {chunk.start:.2f} | End: {chunk.end:.2f}")
        print(f"Text: {chunk.text[:300]}")
        print("-" * 60)


if __name__ == "__main__":
    main()
