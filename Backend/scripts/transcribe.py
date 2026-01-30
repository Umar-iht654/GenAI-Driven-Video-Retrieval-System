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



# Main transcription routine

def main():
    # Check we actually have videos to process
    videos = sorted(VIDEOS_DIR.glob("*.mp4"))
    if not videos:
        raise FileNotFoundError(
            f"No .mp4 files found in {VIDEOS_DIR}. Put videos in Data/videos/"
        )

    # Automatically choose GPU or CPU settings
    device, compute_type = choose_device_and_precision()

    #Set model size to medium for better accuracy for more technical lectures
    #Can set to "small" for faster times but still has good accuracy
    model_size = "medium"

    print(f"Device selected: {device} | compute_type: {compute_type} | model: {model_size}")

    # Create the Whisper model instance (this loads model weights)
    model = WhisperModel(model_size, device=device, compute_type=compute_type)

    # Process every mp4 in Data/videos/
    for video_path in videos:
        out_path = OUT_DIR / f"{video_path.stem}.vtt"

        print(f"\nTranscribing: {video_path.name}")
        print(f"Output:       {out_path.name}")

        # Transcribe the video file
        # beam_size: search width; higher can improve accuracy but slows down
        # vad_filter: skips long silence sections (great for lectures)
        segments_iter, info = model.transcribe(
            str(video_path),
            beam_size=5,
            vad_filter=True,
        )

        # Consume the iterator to a list so we can write it once
        segments = list(segments_iter)

        # Write the subtitles to disk
        write_vtt(segments, out_path)

        # Print basic metadata for logging/debugging
        print(f"Detected language: {info.language}")
        print(f"Audio duration:    {info.duration:.1f}s")
        print(f"Segments written:  {len(segments)}")
        print("Done.")


if __name__ == "__main__":
    main()
