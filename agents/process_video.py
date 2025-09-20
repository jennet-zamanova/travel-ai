import streamlit as st
import tempfile
import subprocess
from openai import OpenAI

from moviepy.editor import VideoFileClip
import os

from agents.get_video_text import extract_text_from_video

def extract_audio(video_path):
    clip = VideoFileClip(video_path)
    audio_path = os.path.splitext(video_path)[0] + ".mp3"
    clip.audio.write_audiofile(audio_path)
    return audio_path


def process_videos(uploaded_files: list):
    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

    for uploaded_file in uploaded_files:
        st.subheader(f"Processing: {uploaded_file.name}")

        # Step 2: Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp_video:
            tmp_video.write(uploaded_file.read())
            video_path = tmp_video.name

        # Step 3: Extract audio with ffmpeg
        audio_path = extract_audio(video_path)

        # Step 4: Transcribe audio
        with open(audio_path, "rb") as f:
            transcript = client.audio.transcriptions.create(
                model="gpt-4o-transcribe",  # or "whisper-1"
                file=f
            )

        # get text from visuals: 
        st.info("Extracting text from video frames…")
        additional_info = extract_text_from_video(video_path)

        transcript = f"Here is the voiceover text: {transcript.text} an here is the additional text displayed visually in the video {additional_info}"

        # Step 5: Summarize transcript
        summary = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Summarize transcripts into clear, concise points."},
                {"role": "user", "content": transcript}
            ]
        )

        # Step 6: Display results
        st.success(f"Summary for {uploaded_file.name}:")
        st.write(summary.choices[0].message.content)