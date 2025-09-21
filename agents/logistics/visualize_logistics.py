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


def visualize_itinerary(plan: TripPlan):

    # Show trip overview
    st.subheader("🌍 Trip Overview")
    st.write(plan.get("trip_overview", ""))

    # Render itinerary as cards/timeline
    st.subheader("🗓 Itinerary")
    itinerary = plan.get("itinerary", [])

    for item in itinerary:
        with st.container():
            st.markdown(f"### Day {item['day_index']}: {item['activity_title']}")
            cols = st.columns([2, 2, 2])

            with cols[0]:
                st.write(f"📍 **Location:** {item['location_name']}")
                st.write(f"🕒 **Time:** {item['start_time']} → {item['end_time']}")
                st.write(f"⏱ **Duration:** {item['duration_minutes']} min")

            with cols[1]:
                st.write(f"🚍 **Transport:** {item['transport_mode']}")
                st.write(f"ℹ️ {item['transport_details']}")
                st.write(f"💰 **Cost:** {item['cost_estimate']}")

            with cols[2]:
                st.write("💡 **Cultural Tips:**")
                for tip in item.get("cultural_tips", []):
                    st.write(f"- {tip}")
                if item.get("notes"):
                    st.write(f"📝 **Notes:** {item['notes']}")

            st.markdown("---")

