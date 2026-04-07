import argparse

from app.script_utils import parse_subtitle


def main():
    parser = argparse.ArgumentParser(
        description="Inspect raw VTT parsing output for a subtitle file."
    )
    parser.add_argument("--video-id", help="Video id to resolve from Data/subtitles/<video_id>.vtt")
    parser.add_argument("--subtitle-path", help="Explicit path to a .vtt subtitle file")
    args = parser.parse_args()

    result = parse_subtitle(
        video_id=args.video_id,
        subtitle_path=args.subtitle_path,
    )

    print(f"Subtitle file: {result['subtitle_path']}")
    print(f"Parsed segments: {len(result['segments'])}")
    print("First 3:")
    for segment in result["segments"][:3]:
        print(f"- {segment.start:.3f} -> {segment.end:.3f}: {segment.text[:80]}")


if __name__ == "__main__":
    main()
