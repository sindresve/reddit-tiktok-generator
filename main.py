import os
import random
import sys
from transcript_generator import get_youtube_transcript

def main():
    if len(sys.argv) < 3:
        print("Missing arguments: youtube_url or output_name")
        sys.exit(1)

    youtube_url = sys.argv[1]
    output_name = sys.argv[2]

    output_path = f"output/{output_name}.txt"
    os.makedirs("output", exist_ok=True)

    try:
        transcript = get_youtube_transcript(youtube_url, output_path)
        if transcript:
            print("Transcript saved successfully.")
            print("DONE")  # Success signal for JS
        else:
            print("Failed to retrieve transcript.")
            sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
