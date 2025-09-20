import streamlit as st

st.title("Welcome to Travel AI 👋")

uploaded_files = st.file_uploader("Upload your collection of reels", accept_multiple_files="directory")
