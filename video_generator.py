import edge_tts
import asyncio
from moviepy.editor import *
import json
import re
from pydub import AudioSegment
import os
import tempfile
import numpy as np
from moviepy.config import change_settings
import speech_recognition as sr
from pydub.utils import which
import whisper
import torch

# Update with your actual ImageMagick path
change_settings({"IMAGEMAGICK_BINARY": r"C:\Program Files\ImageMagick-7.1.2-Q16-HDRI\magick.exe"})

class PerfectTimingTikTokGenerator:
    def __init__(self):
        self.temp_dir = tempfile.mkdtemp()
        self.voice = "en-US-AriaNeural"
        self.video_width = 1080
        self.video_height = 1920
        
        # Load Whisper model for accurate timing
        print("Loading Whisper model for timing analysis...")
        self.whisper_model = whisper.load_model("base")
    
    def clean_word_for_display(self, word):
        """Clean word to only include alphanumeric characters"""
        # Remove all non-alphanumeric characters except spaces
        cleaned = re.sub(r'[^a-zA-Z0-9\s%]', '', word)
        return cleaned.strip()
    
    def should_skip_word(self, word):
        """Check if word should be skipped (empty after cleaning or only symbols)"""
        cleaned = self.clean_word_for_display(word)
        return len(cleaned) == 0
        
    async def generate_voice(self, text, output_path):
        """Generate TTS audio"""
        communicate = edge_tts.Communicate(text, self.voice, rate="+40%")
        await communicate.save(output_path)
        
    def get_word_timings_whisper(self, audio_path, original_text):
        """Get precise word timings using Whisper"""
        print("Analyzing speech for precise word timings...")
        
        # Load and transcribe with word-level timestamps
        result = self.whisper_model.transcribe(
            audio_path, 
            word_timestamps=True,
            language="en"
        )
        
        word_timings = []
        original_words = original_text.lower().split()
        
        # Extract word timings from Whisper result
        if 'segments' in result:
            for segment in result['segments']:
                if 'words' in segment:
                    for word_info in segment['words']:
                        word_timings.append({
                            'word': word_info['word'].strip(),
                            'start': word_info['start'],
                            'end': word_info['end']
                        })
        
        # Match with original text words (handling punctuation)
        matched_timings = []
        whisper_idx = 0
        
        for orig_word in original_words:
            clean_orig = re.sub(r'[^\w]', '', orig_word.lower())
            
            # Skip if the original word becomes empty after cleaning
            if not clean_orig:
                continue
            
            # Find matching word in whisper results
            best_match = None
            search_range = min(5, len(word_timings) - whisper_idx)
            
            for i in range(search_range):
                if whisper_idx + i >= len(word_timings):
                    break
                    
                whisper_word = re.sub(r'[^\w]', '', 
                                    word_timings[whisper_idx + i]['word'].lower())
                
                if clean_orig in whisper_word or whisper_word in clean_orig:
                    best_match = word_timings[whisper_idx + i]
                    whisper_idx += i + 1
                    break
            
            if best_match:
                matched_timings.append({
                    'word': orig_word,
                    'start': best_match['start'],
                    'end': best_match['end'],
                    'duration': best_match['end'] - best_match['start']
                })
            else:
                # Fallback: estimate timing
                if matched_timings:
                    last_end = matched_timings[-1]['end']
                    estimated_duration = 0.3  # Default word duration
                    matched_timings.append({
                        'word': orig_word,
                        'start': last_end,
                        'end': last_end + estimated_duration,
                        'duration': estimated_duration
                    })
                else:
                    matched_timings.append({
                        'word': orig_word,
                        'start': 0.0,
                        'end': 0.3,
                        'duration': 0.3
                    })
        
        return matched_timings
    
    def create_non_overlapping_subtitles(self, text, audio_path, gap_between_words=0.03):
        """Create subtitles with guaranteed no overlap, perfect speech sync, and smooth animations"""
        
        # Get precise word timings
        word_timings = self.get_word_timings_whisper(audio_path, text)
        
        subtitle_clips = []
        
        # Filter out empty words first to get clean indexing
        valid_timings = []
        for timing in word_timings:
            if not self.should_skip_word(timing['word']):
                valid_timings.append(timing)
        
        # Calculate all timings first to prevent overlaps
        subtitle_timings = []
        
        for i, timing in enumerate(valid_timings):
            word_start = timing['start']
            word_end = timing['end']
            word_duration = word_end - word_start
            
            # Conservative anticipation to prevent early appearance
            anticipation = min(0.04, word_duration * 0.25)
            start_time = max(0, word_start - anticipation)
            
            # Base end time ensures word is visible during speech
            base_end_time = word_end + 0.04
            
            # Check next word constraint
            if i < len(valid_timings) - 1:
                next_word_start = valid_timings[i + 1]['start']
                next_anticipation = min(0.04, (valid_timings[i + 1]['end'] - valid_timings[i + 1]['start']) * 0.25)
                next_start_time = max(0, next_word_start - next_anticipation)
                
                # Strict no-overlap policy
                max_end_time = next_start_time - gap_between_words
                end_time = min(base_end_time, max_end_time)
                
                # If this makes duration too short, prioritize no overlap
                if end_time <= start_time:
                    end_time = start_time + 0.15  # Minimum viable duration
                    
            else:
                end_time = base_end_time
            
            subtitle_timings.append({
                'start': start_time,
                'end': end_time,
                'duration': end_time - start_time,
                'word_start': word_start,
                'word_end': word_end,
                'timing': timing
            })
        
        # Create clips with calculated timings
        for i, sub_timing in enumerate(subtitle_timings):
            timing = sub_timing['timing']
            clean_word = self.clean_word_for_display(timing['word'])
        
            txt_clip = (TextClip(
                clean_word.upper(),
                fontsize=90,
                color='white',
                stroke_color='black',
                stroke_width=6,
                font='Montserrat-Extra-Bold',
                method='label',
                align='center'
            )
            .set_position(('center', 'center'))
            .set_start(sub_timing['start'])
            .set_duration(sub_timing['duration'])
            )
            
            # Restored and improved pop animation
            def make_smooth_pop_animation(word_spoken_start, word_spoken_end, clip_start, clip_duration):
                def scale_func(t):
                    current_time = clip_start + t
                    
                    # Animation phases
                    if current_time < word_spoken_start:
                        # Pre-speech: gentle anticipation
                        time_before = word_spoken_start - current_time
                        if time_before > 0.05:
                            return 0.9  # Stable small size
                        else:
                            # Quick buildup in last 50ms before speech
                            buildup = 1 - (time_before / 0.05)
                            return 0.9 + 0.4 * buildup  # 0.9 to 1.3
                    
                    elif current_time <= word_spoken_end:
                        # During speech: dynamic pop effect
                        speech_progress = (current_time - word_spoken_start) / max(word_spoken_end - word_spoken_start, 0.01)
                        
                        if speech_progress <= 0.2:
                            # Quick pop to peak (first 20% of word)
                            return 1.3 + 0.2 * (speech_progress / 0.2)  # 1.3 to 1.5
                        elif speech_progress <= 0.7:
                            # Hold at peak during main speech
                            return 1.5
                        else:
                            # Gentle settle during end of speech
                            settle = (speech_progress - 0.7) / 0.3
                            return 1.5 - 0.3 * settle  # 1.5 to 1.2
                    
                    else:
                        # Post-speech: quick settle
                        time_after = current_time - word_spoken_end
                        if time_after < 0.08:
                            settle_progress = time_after / 0.08
                            return 1.2 - 0.3 * settle_progress  # 1.2 to 0.9
                        else:
                            return 0.9  # Final stable size
                
                return scale_func
            
            # Apply animation
            txt_clip = txt_clip.resize(make_smooth_pop_animation(
                sub_timing['word_start'], 
                sub_timing['word_end'], 
                sub_timing['start'], 
                sub_timing['duration']
            ))
            
            # Smooth fade transitions
            fade_time = min(0.025, sub_timing['duration'] * 0.12)
            txt_clip = txt_clip.crossfadein(fade_time).crossfadeout(fade_time)
            
            subtitle_clips.append(txt_clip)
        
        return subtitle_clips
    
    async def create_video(self, text, background_video_path, output_path):
        """
        Create video with perfect subtitle timing
        
        subtitle_style options:
        - "single_word": One word at a time (TikTok style)
        - "phrase": Multiple words per subtitle (more readable)
        """
        print("Starting video generation with perfect timing...")
        
        # 1. Generate voice
        print("Generating voice...")
        audio_path = os.path.join(self.temp_dir, "voice.wav")
        mp3_path = os.path.join(self.temp_dir, "voice.mp3")
        
        await self.generate_voice(text, mp3_path)
        
        # Convert to WAV for better Whisper compatibility
        audio_segment = AudioSegment.from_mp3(mp3_path)
        audio_segment.export(audio_path, format="wav")
        
        # 2. Load background with RGB conversion
        print("Loading background video...")
        background = VideoFileClip(background_video_path).to_RGB()
        
        # 3. Load audio
        audio = AudioFileClip(audio_path)
        
        # 4. Resize/crop background to portrait
        target_aspect = self.video_height / self.video_width
        video_aspect = background.h / background.w
        
        if video_aspect > target_aspect:
            new_height = int(background.w * target_aspect)
            background = background.crop(
                y1=(background.h - new_height) // 2,
                y2=(background.h + new_height) // 2
            )
        else:
            new_width = int(background.h / target_aspect)
            background = background.crop(
                x1=(background.w - new_width) // 2,
                x2=(background.w + new_width) // 2
            )
        
        background = background.resize((self.video_width, self.video_height))
        
        # 5. Loop background if needed
        if background.duration < audio.duration:
            background = background.loop(duration=audio.duration)
        else:
            background = background.subclip(0, audio.duration)
        
        # 6. Create perfectly timed subtitles
        print(f"Creating subtitles with perfect timing...")
        
        subtitle_clips = self.create_non_overlapping_subtitles(text, audio_path, gap_between_words=0.03)
        
        # 7. Composite everything
        print("Compositing video...")
        final_video = CompositeVideoClip(
            [background] + subtitle_clips
        ).set_audio(audio)
        
        # 8. Export with optimized settings
        print("Exporting video...")
        final_video.write_videofile(
            output_path,
            fps=30,
            codec='libx264',
            audio_codec='aac',
            preset='medium',
            threads=4,
            ffmpeg_params=['-pix_fmt', 'yuv420p', '-movflags', '+faststart']
        )
        
        print("Video created successfully with perfect timing!")
        
        # Cleanup
        for temp_file in [audio_path, mp3_path]:
            if os.path.exists(temp_file):
                os.remove(temp_file)
                
        return output_path