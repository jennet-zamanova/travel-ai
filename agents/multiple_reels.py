import os
from openai import OpenAI
import streamlit as st
import tempfile

from moviepy.editor import VideoFileClip
import os

import base64

def image_to_data_url(path):
    with open(path, "rb") as f:
        data = base64.b64encode(f.read()).decode("utf-8")
    return f"data:image/jpeg;base64,{data}"


client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

def extract_audio(video_path):
    clip = VideoFileClip(video_path)
    audio_path = os.path.splitext(video_path)[0] + ".mp3"
    clip.audio.write_audiofile(audio_path)
    return audio_path


def process_reel(video_path):
    """
    Extracts audio + creates montage for a reel.
    Returns dict with both paths.
    """
    # Extract audio track
    audio_path = extract_audio(video_path)

    # Transcribe audio
    with open(audio_path, "rb") as f:
        transcript = client.audio.transcriptions.create(
            model="gpt-4o-mini-transcribe",
            file=f
        ).text

    # Create montage
    montage_path = create_montage_from_video(video_path, frame_interval=2, grid_width=3)

    return {
        "video": video_path,
        "montage": montage_path,
        "transcript": transcript,
    }

def summarize_reel_batch(reels_batch):
    """
    Sends a batch of reels (montage + transcript) to GPT for summary.
    """
    st.write("request 1")
    messages = [
        {
            "role": "system", 
            "content":(
                "You are an assistant that analyzes user reels (transcripts + images) "
                "and produces a structured JSON summary. "
                "The JSON must strictly follow this schema:\n\n"
                "{\n"
                '  "summary": "string",\n'
                '  "keywords": ["string", ...],\n'
                '  "locations": [\n'
                "     {\"name\": \"string\", \"rating\": \"string or null\"}, ...\n"
                "  ]\n"
                "}\n\n"
                "Rules:\n"
                "- Always output valid JSON only (no extra text).\n"
                "- `summary`: a concise text summary of the user’s travel preferences.\n"
                "- `keywords`: 5–10 travel-related keywords extracted from reels.\n"
                "- `locations`: every location mentioned, each with an optional rating if present; if not, use null.\n"
            )
        }
        ]

    for i, reel in enumerate(reels_batch, 1):

        messages.append({
            "role": "user",
            "content": [
                {"type": "text", "text": f"Reel {i} transcript:\n{reel['transcript']}"},
                {"type": "image_url", "image_url": {"url": image_to_data_url(reel["montage"])}}
            ]
        })


    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        response_format={"type": "json_object"},
    )
    return response.choices[0].message.content

def process_all_reels(video_paths, batch_size=3):
    results = []
    batch = []

    for uploaded_file in video_paths:
        st.subheader(f"Processing: {uploaded_file.name}")

        # Step 2: Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp_video:
            tmp_video.write(uploaded_file.read())
            video_path = tmp_video.name

        reel_data = process_reel(video_path)
        batch.append(reel_data)

        if len(batch) == batch_size:
            results.append(summarize_reel_batch(batch))
            st.success(f"Summary for {uploaded_file.name}:")
            st.write(results[-1])
            batch = []

    # Process leftover batch
    if batch:
        results.append(summarize_reel_batch(batch))

    return results

import cv2
import math
import tempfile
from PIL import Image
import os

def create_montage_from_video(video_path, frame_interval=2, grid_width=3):
    """
    Create a montage from a video by extracting 1 frame every `frame_interval` seconds.
    
    Args:
        video_path (str): Path to video file (e.g. .mp4).
        frame_interval (int): Interval in seconds between frames to extract.
        grid_width (int): Number of columns in the montage grid.
    
    Returns:
        str: Path to the saved montage image.
    """
    # Extract frames every `frame_interval` seconds
    vidcap = cv2.VideoCapture(video_path)
    fps = int(vidcap.get(cv2.CAP_PROP_FPS)) or 1
    step = fps * frame_interval
    frames = []
    count, saved = 0, 0

    tmpdir = tempfile.mkdtemp()

    while True:
        success, image = vidcap.read()
        if not success:
            break
        if count % step == 0:
            frame_path = os.path.join(tmpdir, f"frame_{saved}.jpg")
            cv2.imwrite(frame_path, image)
            frames.append(frame_path)
            saved += 1
        count += 1

    vidcap.release()

    if not frames:
        raise ValueError("No frames extracted from video!")

    # Load extracted frames
    images = [Image.open(f) for f in frames]
    w, h = images[0].size
    images = [img.resize((w, h)) for img in images]

    # Compute grid
    cols = grid_width
    rows = math.ceil(len(images) / cols)
    montage = Image.new('RGB', (cols*w, rows*h), color=(0, 0, 0))

    for idx, img in enumerate(images):
        x = (idx % cols) * w
        y = (idx // cols) * h
        montage.paste(img, (x, y))

    # Save montage
    montage_path = os.path.join(tmpdir, "montage.jpg")
    montage.save(montage_path)

    return montage_path
