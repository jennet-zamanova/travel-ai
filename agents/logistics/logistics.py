import json
from typing import Any, Dict, List
import streamlit as st
from openai import OpenAI
import re

from typing import List, Literal, Optional, TypedDict


TransportMode = Literal["walk", "bus", "metro", "train", "taxi", "rideshare", "bike", "ferry", "flight", "none"]


class ItineraryItem(TypedDict):
    day_index: int
    date: Optional[str]  # ISO YYYY-MM-DD or None
    start_time: Optional[str]  # ISO HH:MM:SS or None
    end_time: Optional[str]  # ISO HH:MM:SS or None
    activity_title: str
    location_name: str
    transport_mode: TransportMode
    transport_details: str  # "N/A" if not moving
    duration_minutes: int
    cost_estimate: str
    cultural_tips: List[str]  # 1–3 short strings
    notes: str  # "" if none


class TripPlan(TypedDict):
    trip_overview: str
    itinerary: List[ItineraryItem]


client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
def build_prompt(location_dates: Dict[str, Dict[str, str]], preferences: str, transport_options: List[str], travelers: int, locations: List[str]) -> str:
    """Create an LLM prompt that requests both a human-readable itinerary and a strict JSON block.


    We ask the model to emit a JSON block with a top-level `itinerary` array and also a markdown-friendly explanation.
    """
    # short description of location order
    loc_str = "\n".join([f"- {loc} ({dates['start']} to {dates['end']})" for loc, dates in location_dates.items()])



    system = (
    "You are an expert travel planner. Given the trip specification below, produce two outputs separated clearly:\n"
    "1) A JSON block wrapped in triple backticks labeled as ```json``` that contains a STRICT machine-readable itinerary.\n"
    "2) A human-readable markdown itinerary summary suitable for sending to the traveler.\n\n"
    "STRICT JSON REQUIREMENTS:\n"
    "- Top-level object must include:\n"
    "   - `trip_overview` (string, 1–2 sentences)\n"
    "   - `itinerary` (array of objects)\n"
    "- Each itinerary item object must contain ALL of these fields (no omissions, no extra keys):\n"
    "   - `day_index` (integer, starting from 1)\n"
    "   - `date` (string, ISO format YYYY-MM-DD if known, otherwise null)\n"
    "   - `start_time` (string, ISO 24h time HH:MM:SS if known, otherwise null)\n"
    "   - `end_time` (string, ISO 24h time HH:MM:SS if known, otherwise null)\n"
    "   - `activity_title` (string, concise name of activity)\n"
    "   - `location_name` (string, place or venue)\n"
    "   - `transport_mode` (string, one of: walk, bus, metro, train, taxi, rideshare, bike, ferry, flight, none)\n"
    "   - `transport_details` (string, must include booking info or travel duration if applicable, otherwise 'N/A')\n"
    "   - `duration_minutes` (integer, >=0)\n"
    "   - `cost_estimate` (string, e.g., 'Free', '£20-30 per person')\n"
    "   - `cultural_tips` (array of 1–3 short strings, each under 120 characters)\n"
    "   - `notes` (string, optional advice or remarks; if none, use empty string)\n\n"
    "VALIDATION RULES:\n"
    "- All fields must appear, even if null or empty.\n"
    "- No trailing commas, no comments, must be valid JSON.\n"
    "- Ensure logical consistency: start_time < end_time, duration_minutes matches the difference when possible.\n"
    "- Prefer public transport when available. Assume moderate budget unless specified.\n\n"
    "After the JSON section, write a concise but engaging MARKDOWN itinerary summary for the traveler with times, travel instructions, and cultural tips for each stop.\n"
)



    user_section = (
    f"Trip cities:\n{loc_str}\n\n"
    f"Locations to visit:\n{', '.join(locations)}\n\n"
    f"Traveler preferences: {preferences}\n"
    f"Allowed transport modes: {', '.join(transport_options)}\n"
    f"Number of travelers: {travelers}\n\n"
    "Return the JSON in a single ```json``` fenced code block and then the markdown itinerary."
    )


    full_prompt = system + "\n" + user_section
    return full_prompt

def extract_json_from_text(text: str) -> Any:
    """Try to find the first JSON block in text and load it."""
    # find triple-backtick json block
    m = re.search(r"```json\s*(\{.*?\})\s*```", text, flags=re.S)
    if not m:
        # fallback: try to find first `{...}` large chunk
        m2 = re.search(r"(\{\s*\"trip_overview\".*\})", text, flags=re.S)
        if not m2:
            # last resort: try to find any JSON-like object
            try:
                return json.loads(text)
            except Exception:
                return None
        else:
            try:
                return json.loads(m2.group(1))
            except Exception:
                return None
    try:
        return json.loads(m.group(1))
    except Exception:
        return None
    
def generate_itinerary(location_dates, locations, preferences, transport_options, travelers, temperature=0.2, max_tokens=2000, model="gpt-4o-mini"):
    if OpenAI is None:
        st.error("openai client library not available. Please `pip install openai` and restart the app.")
    else:
        prompt = build_prompt(location_dates, preferences, transport_options, travelers, locations)

    with st.spinner("Generating itinerary — this may take a few seconds..."):
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                {"role": "system", "content": "You are a helpful travel planning assistant."},
                {"role": "user", "content": prompt},
                ],
                temperature=float(temperature),
                max_tokens=int(max_tokens),
            )


            # The exact shape depends on the OpenAI client version. We expect `response.choices[0].message.content`.
            raw_text = response.choices[0].message.content


            st.subheader("Raw model output")
            st.code(raw_text[:100], language="markdown")


            parsed = extract_json_from_text(raw_text)
            if parsed:
                return parsed
            else:
                st.warning("Could not extract machine-readable JSON from the response. The raw output is shown above.")


        except Exception as e:
            st.error(f"Error while calling the LLM: {e}")
