import streamlit as st

from agents.multiple_reels import process_all_reels
from agents.process_video import process_videos

st.title("Welcome to Travel AI 👋")

uploaded_files = st.file_uploader("Upload your collection of reels", type=["mp4", "mov", "avi"], accept_multiple_files=True)

if uploaded_files:
    # process_videos(uploaded_files)
    summary = process_all_reels(uploaded_files)
    st.write("here is the summary: ")
    st.write(summary)