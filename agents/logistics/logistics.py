import json
from typing import Any, Dict, List
import streamlit as st
from openai import OpenAI
import re

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
def build_prompt(location_dates: Dict[str, Dict[str, str]], preferences: str, transport_options: List[str], travelers: int, locations: List[str]) -> str:
    """Create an LLM prompt that requests both a human-readable itinerary and a strict JSON block.


    We ask the model to emit a JSON block with a top-level `itinerary` array and also a markdown-friendly explanation.
    """
    # short description of location order
    loc_str = "\n".join([f"- {loc} ({dates['start']} to {dates['end']})" for loc, dates in location_dates.items()])



    system = (
    "You are an expert travel planner. Given the trip specification below, produce two outputs separated clearly:\n"
    "1) A JSON block wrapped in triple backticks labeled as ```json``` that contains a machine-readable itinerary for the traveler. "
    "2) A human-readable markdown itinerary summary suitable for sending to the traveler.\n\n"
    "REQUIREMENTS for the JSON:\n"
    "- Top-level keys: `trip_overview` (brief), `itinerary` (array).\n"
    "- Each itinerary item must include: `day_index`, `date` (ISO YYYY-MM-DD if possible), `start_time` (ISO time if available), `end_time`, `activity_title`, `location_name`, `transport_mode` (if moving), `transport_details` (how to book, duration), `duration_minutes`, `cost_estimate` (string), `cultural_tips` (array of short tips), `notes`.\n"
    "- After the JSON section, include a readable markdown itinerary with times, travel instructions, and cultural tips for each stop.\n\n"
    "Be concise but specific: include recommended transport lines (e.g., train names or typical journey times), suggested time blocks for visits, and 2-3 cultural tips per city (short). If the input lacks dates, create a day-by-day plan in logical order. Prioritize public transport when allowed. Assume moderate budget unless user says otherwise.\n\n"
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
                st.subheader("Parsed JSON itinerary")
                st.json(parsed)


                st.download_button(
                "Download itinerary JSON",
                data=json.dumps(parsed, indent=2),
                file_name="itinerary.json",
                mime="application/json",
                )
            else:
                st.warning("Could not extract machine-readable JSON from the response. The raw output is shown above.")


        except Exception as e:
            st.error(f"Error while calling the LLM: {e}")


# def visualize_itinerary(itinerary):
