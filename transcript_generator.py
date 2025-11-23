import re
from youtube_transcript_api import YouTubeTranscriptApi

def get_youtube_transcript(video_url, output_path):
    try:
        video_id = video_url.split("v=")[1].split("&")[0]
        
        fetched_transcript = YouTubeTranscriptApi().fetch(video_id)
        transcript = fetched_transcript.to_raw_data()
        
        full_text = " ".join([entry["text"] for entry in transcript])
        cleaned_text = re.sub(r"[^a-zA-Z0-9,.!?'\s]", '', full_text)
        
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(cleaned_text)
        
        return cleaned_text
    except Exception as e:
        print(f"Error: {e}")
        return None
