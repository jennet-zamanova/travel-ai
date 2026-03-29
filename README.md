# Travel AI

Travel AI is a Streamlit-based trip planning assistant powered by OpenAI. It takes your travel preferences, optional video reels, and budget to generate style-matched place recommendations, a budget-optimized selection, and a fully structured day-by-day itinerary.

## Features

- **Multi-step wizard UI** — A guided Streamlit interface that walks you through city selection, date ranges, traveler count, transport preferences, and free-text style preferences.
- **Video reel ingestion** — Upload short travel video clips; the app extracts audio, transcribes it, builds image montages from frames, and uses a multimodal LLM to extract structured preferences, keywords, and locations with ratings.
- **Style-based recommendations** — For each destination city, an AI agent returns 10–15 places tailored to your stated travel style (e.g., romantic, adventurous, foodie).
- **Budget optimization** — A budget agent scores and ranks recommended places by estimated cost and review quality, greedily selecting the best set that fits within your total budget.
- **Itinerary generation** — Produces a structured JSON trip plan (`trip_overview` + per-day `itinerary` with times, transport modes, costs, and tips) and renders it in a clean Streamlit layout.
- **Export** — Download the final trip plan as a JSON file.

## Tech Stack

| Layer | Technology |
|-------|-----------|
| UI | [Streamlit](https://streamlit.io/) |
| AI / LLM | [OpenAI Python SDK](https://github.com/openai/openai-python) (`gpt-4o-mini`, `gpt-5`) |
| Audio transcription | OpenAI `gpt-4o-mini-transcribe` |
| Video processing | [MoviePy](https://zulko.github.io/moviepy/), [OpenCV](https://opencv.org/) |
| Image processing | [Pillow](https://python-pillow.org/) |
| Config | TOML secrets (`.streamlit/secrets.toml`, `secret/keys.local.toml`) |

## Prerequisites

- Python 3.11+ (recommended; 3.8+ may work with `tomli` installed separately)
- An OpenAI API key
- [FFmpeg](https://ffmpeg.org/download.html) installed on your system (required by MoviePy for audio extraction)

## Installation

1. **Clone the repository:**

   ```bash
   git clone https://github.com/your-username/travel-ai.git
   cd travel-ai
   ```

2. **Install the dependencies:**

   ```bash
   pip install streamlit openai moviepy opencv-python pillow
   ```

   On Python < 3.11, also install `tomli`:

   ```bash
   pip install tomli
   ```

## Configuration

The app reads your OpenAI API key from Streamlit secrets. Create the secrets file before running:

```bash
mkdir -p .streamlit
```

Then create `.streamlit/secrets.toml` with:

```toml
OPENAI_API_KEY = "sk-..."
```

> This file is gitignored and will never be committed.

**Optional — StyleAgent TOML config:**
The `StyleAgent` also supports a separate key file at `secret/keys.local.toml`:

```toml
[openai]
api_key = "sk-..."
model = "gpt-5"   # optional, defaults to gpt-5
```

If neither the TOML file nor `OPENAI_API_KEY` environment variable is set, the StyleAgent falls back to `st.secrets`.

## Running the App

```bash
streamlit run main.py
```

This starts a local Streamlit server and opens the app in your browser.

### Wizard steps

| Step | Description |
|------|-------------|
| 1 | Enter destination cities |
| 2 | Set date ranges per city |
| 3 | Enter traveler count, budget, transport preferences, and free-text style |
| 4 | (Optional) Upload travel video reels for preference extraction |
| 5 | Generate style recommendations → budget optimization → itinerary |
| 6 | View the itinerary and download it as JSON |

## Project Structure

```
travel-ai/
├── main.py                          # Streamlit app entry point and wizard flow
├── agents/
│   ├── style_agent.py               # StyleAgent: LLM-based place recommendations per city
│   ├── budget_agent.py              # Budget agent: cost/review scoring and place selection
│   ├── multiple_reels.py            # Reel pipeline: audio extraction, transcription, montage, summarization
│   ├── process_video.py             # (WIP) Single-video processing pipeline
│   └── logistics/
│       ├── logistics.py             # Itinerary generation and JSON extraction
│       └── visualize_logistics.py   # Streamlit rendering of the trip plan
```

## Agents

- **`StyleAgent`** (`agents/style_agent.py`) — Given a city and a style description, calls the chat model and returns a validated JSON object with `places` (newline-separated names) and `locations` (structured array). Supports TOML, env var, and `st.secrets` for API key loading.

- **`budget_agent`** (`agents/budget_agent.py`) — Merges required places (from reels) and optional style-recommended places, fetches per-place cost and review score from `gpt-4o-mini`, then greedily fills the budget. Returns a ranked, budget-fitted list.

- **`multiple_reels`** (`agents/multiple_reels.py`) — For each uploaded video: saves to a temp file, extracts audio with MoviePy, transcribes with OpenAI, extracts frames and assembles a montage grid with OpenCV + Pillow, then sends the transcript + montage to `gpt-4o-mini` for structured preference/location extraction. Processes in batches of 3.

- **`logistics`** (`agents/logistics/logistics.py`) — Builds a detailed planner prompt and calls `gpt-4o-mini` for a strict JSON itinerary. Parses fenced ` ```json ``` ` blocks with a fallback to bare `{...}` extraction. Defines `TripPlan` and `ItineraryItem` TypedDicts.

- **`visualize_logistics`** (`agents/logistics/visualize_logistics.py`) — Renders the parsed trip plan in Streamlit with per-day activity cards.

- **`process_video`** (`agents/process_video.py`) — WIP single-video pipeline; currently has a missing dependency (`get_video_text`) and is not wired into the main app.
