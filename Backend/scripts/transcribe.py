#Transcribe local .mp4 lecture videos into .vtt subtitle files.

#Looks for videos in:  <project-root>/Data/videos/*.mp4
#Saves subtitles to:   <project-root>/Data/subtitles/<video_name>.vtt
#Uses NVIDIA GPU (CUDA) if available, otherwise uses CPU.


from pathlib import Path  # Cross-platform file path handling
import torch              #Used only to detect if GPU is available
from faster_whisper import WhisperModel  #Fast Whisper implementation


#Path setup (project folders)

#Resolve this script's location on disk, then move up to the project root.
#scripts/transcribe_auto.py -> Backend/scripts -> Backend -> project-root
ROOT = Path(__file__).resolve().parents[2]

#Folder containing local lecture videos
VIDEOS_DIR = ROOT / "Data" / "videos"

#Folder where we will save the generated subtitle files
OUT_DIR = ROOT / "Data" / "subtitles"
OUT_DIR.mkdir(parents=True, exist_ok=True)  # Create output folder if missing


# Helper functions

def seconds_to_vtt_timestamp(seconds: float) -> str:

    #Convert seconds (float) to WebVTT timestamp format: HH:MM:SS.mmm
    #Example: 83.25 -> "00:01:23.250"
    
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = seconds % 60  # keep fractional milliseconds
    return f"{hours:02d}:{minutes:02d}:{secs:06.3f}"


def write_vtt(segments, out_path: Path) -> None:
    
    #Write transcription segments to a .vtt file.
    #Each segment has start time, end time, and text.
    
    with out_path.open("w", encoding="utf-8") as f:
        f.write("WEBVTT\n\n")  # WebVTT file header

        for seg in segments:
            #Convert numeric timestamps to VTT format
            start = seconds_to_vtt_timestamp(seg.start)
            end = seconds_to_vtt_timestamp(seg.end)

            #Clean up text and avoid accidentally writing the VTT arrow token inside text
            text = seg.text.strip().replace("-->", "->")

            #Write one caption block: time range + text + blank line
            f.write(f"{start} --> {end}\n{text}\n\n")


def choose_device_and_precision() -> tuple[str, str]:
    
    #Decide whether to use GPU or CPU automatically.
    #device: "cuda" if NVIDIA GPU is available, else "cpu"
    
    if torch.cuda.is_available():
        # GPU available: float16 is fast and accurate on modern NVIDIA cards
        return "cuda", "float16"
    else:
        # CPU mode: int8 is typically faster and uses less memory than float32
        return "cpu", "int8"

def transcribe_video(video_path: Path, model: WhisperModel) -> Path:
    # Build output subtitle path using the same filename stem as the video
    out_path = OUT_DIR / f"{video_path.stem}.vtt"

    print(f"\nTranscribing: {video_path.name}")
    print(f"Output:       {out_path.name}")

    # Transcribe the video file
    segments_iter, info = model.transcribe(
        str(video_path),
        beam_size=5,
        vad_filter=True,
    )

    # Convert the generator into a list so it can be written to the .vtt file
    segments = list(segments_iter)

    # Write subtitle file to disk
    write_vtt(segments, out_path)

    # Print metadata for debugging/logging
    print(f"Detected language: {info.language}")
    print(f"Audio duration:    {info.duration:.1f}s")
    print(f"Segments written:  {len(segments)}")
    print("Done.")

    return out_path

def load_whisper_model(model_size: str = "medium") -> WhisperModel:
    # Automatically choose device and precision
    device, compute_type = choose_device_and_precision()

    print(f"Device selected: {device} | compute_type: {compute_type} | model: {model_size}")

    # Create and return the Whisper model
    return WhisperModel(model_size, device=device, compute_type=compute_type)

# Main transcription routine

def main():
    # Check we actually have videos to process
    videos = sorted(VIDEOS_DIR.glob("*.mp4"))
    if not videos:
        raise FileNotFoundError(
            f"No .mp4 files found in {VIDEOS_DIR}. Put videos in Data/videos/"
        )

    # Load the Whisper model once and reuse it for all videos
    model = load_whisper_model(model_size="medium")

    # Process every mp4 in Data/videos/
    for video_path in videos:
        transcribe_video(video_path, model)


if __name__ == "__main__":
    main()
