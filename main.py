import json
import streamlit as st

from agents.logistics.logistics import extract_json_from_text, generate_itinerary
from agents.multiple_reels import process_all_reels
from agents.process_video import process_videos

st.title("Welcome to Travel AI 👋")

st.subheader("Trip specification")
# col1, col2 = st.columns([2, 1])
# with col1:
#     # locations_text = st.text_area(
#     # "Locations and rough time windows (one per line). Example: `Paris, France | 2025-10-01 to 2025-10-05` or `Kyoto - 2026-04-05 (2 days)`",
#     # height=140,
#     # value="Paris, France | 2025-10-01 to 2025-10-05\nLyon, France | 2025-10-06 to 2025-10-07",
#     # )

#     # Allow user to dynamically add any city they want
#     st.markdown("### Add Locations")
#     num_locations = st.number_input("How many locations do you want to add?", min_value=1, max_value=20, value=2)

#     location_dates = {}
#     for i in range(num_locations):
#         st.markdown(f"#### Location {i+1}")
#         city = st.text_input(f"Enter city {i+1}", key=f"city_{i}")
#         col11, col12 = st.columns(2)
#         with col11:
#             start = st.date_input(f"Start date for {city or 'this city'}", key=f"start_{i}")
#         with col12:
#             end = st.date_input(f"End date for {city or 'this city'}", key=f"end_{i}")
#         if city:
#             location_dates[city] = {"start": start.isoformat() if start else None, "end": end.isoformat() if end else None}


#     preferences = st.text_area(
#     "Traveler preferences (food, pace, accessibility, budget, interests)",
#     value="Slow-paced, food + museums, sustainable travel, public transport preferred",
#     height=120,
#     )


# with col2:
#     start_date = st.date_input("Trip start date (optional)", value=None)
#     end_date = st.date_input("Trip end date (optional)", value=None)
#     travelers = st.number_input("Number of travelers", min_value=1, max_value=20, value=1)
#     transport_options = st.multiselect(
#         "Allowed transport modes (app will prioritize these)",
#         options=["train", "bus", "flight", "car", "bike", "walk", "ferry"],
#         default=["train", "walk", "bus"],
#     )


# st.markdown("---")


# ---------- Step 1: Enter locations ----------
step = st.session_state.get("step", 1)

if step == 1:
    st.header("Step 1: Where do you want to go?")
    num_locations = st.number_input("How many locations do you want to add?", min_value=1, max_value=20, value=2)
    cities = []
    for i in range(num_locations):
        city = st.text_input(f"Enter city {i+1}", key=f"city_{i}")
        if city:
            cities.append(city)
    if st.button("Next: Add dates"):
        if cities:
            st.session_state["cities"] = cities
            st.session_state["step"] = 2
            st.rerun()

        else:
            st.warning("Please enter at least one city.")

# ---------- Step 2: Dates for each city ----------
elif step == 2:
    st.header("Step 2: Select travel dates for each city")
    cities = st.session_state.get("cities", [])
    location_dates = {}
    for city in cities:
        st.markdown(f"#### {city}")
        col1, col2 = st.columns(2)
        with col1:
            start = st.date_input(f"Start date for {city}", key=f"start_{city}")
        with col2:
            end = st.date_input(f"End date for {city}", key=f"end_{city}")
        location_dates[city] = {"start": start.isoformat() if start else None, "end": end.isoformat() if end else None}
    if st.button("Next: Preferences"):
        st.session_state["location_dates"] = location_dates
        st.session_state["step"] = 3
        st.rerun()


# ---------- Step 3: Preferences ----------
elif step == 3:
    st.header("Step 3: Traveler preferences")
    preferences = st.text_area(
        "Enter your travel preferences (food, pace, accessibility, budget, interests)",
        value="Slow-paced, food + museums, sustainable travel, public transport preferred",
        height=120,
    )
    travelers = st.number_input("Number of travelers", min_value=1, max_value=20, value=1)
    transport_options = st.multiselect(
        "Allowed transport modes (app will prioritize these)",
        options=["train", "bus", "flight", "car", "bike", "walk", "ferry"],
        default=["train", "walk", "bus"],
    )

    if st.button("Upload Reels Collection"):
        st.session_state["preferences"] = preferences
        st.session_state["travelers"] = travelers
        st.session_state["transport_options"] = transport_options
        st.session_state["step"] = 4
        st.rerun()

elif step == 4:
    st.header("Step 4: Upload Reels")
    uploaded_files = st.file_uploader("Upload your collection of reels", type=["mp4", "mov", "avi"], accept_multiple_files=True)

    if uploaded_files:
        # process_videos(uploaded_files)
        summary = process_all_reels(uploaded_files)
        parsed_summary = extract_json_from_text(summary[0])

        st.subheader("Parsed JSON locations")
        
        parsed_locations = []
        for location in parsed_summary["locations"]:
            parsed_locations.append(location["name"])
        st.json(parsed_locations)

        st.session_state["summary"] = parsed_summary.get("summary", "")
        st.session_state["locations"] = parsed_locations
        st.session_state["locations_and_ratings"] = parsed_summary.get("locations", {})
        st.session_state["step"] = 5
        st.rerun()

elif step == 5:
    st.header("Step 5: Generate Itinerary")
    location_dates = st.session_state.get("location_dates", {})
    preferences = st.session_state.get("preferences", "")
    travelers = st.session_state.get("travelers", 1)
    transport_options = st.session_state.get("transport_options", [])
    summary = st.session_state.get("summary", "")
    locations = st.session_state.get("locations", [])
    locations_and_ratings = st.session_state.get("locations_and_ratings", {})

    if st.button("Generate Itinerary"):
        # process_videos(uploaded_files)
        
        generate_itinerary(location_dates, locations, preferences, transport_options, travelers)
        # st.session_state["step"] = 5






# ---------- Generation and output ----------

# if st.button("Generate Itinerary"):
    # generate_itinerary([], preferences, transport_options, travelers, start_date, end_date)

    