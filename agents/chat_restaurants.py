import openai
from openai import OpenAI
import streamlit as st

def build_prompt(dietary_restrictions: str, location: str) -> str:
    """
    Build a prompt for OpenAI API to generate restaurant suggestions
    with Google Maps links based on dietary restrictions and location.
    """
    prompt = f"""
    You are a helpful restaurant recommendation assistant.
    Please provide a list of at least 5 restaurants in {location}
    that are suitable for someone with the following dietary restrictions:
    {dietary_restrictions}.
    
    Requirements:
    - Return only the restaurant names (no links, no descriptions).
    - Each restaurant should be on its own line.
    - Do not include anything else besides the list.
    - Return the JSON in a single ```json``` fenced code block.
    """
    return prompt.strip()


def get_restaurant_suggestions(dietary_restrictions: str, location: str):
    """
    Query OpenAI with a constructed prompt and return restaurant suggestions.
    """
    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

    prompt = build_prompt(dietary_restrictions, location)

    response = client.chat.completions.create(
        model="gpt-4.1",  # or latest GPT-4.x model
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7
    )

    return response.choices[0].message.content



# Example usage
if __name__ == "__main__":
    dietary_restrictions = "vegan, gluten-free"
    location = "Berlin, Germany"
    
    suggestions = get_restaurant_suggestions(dietary_restrictions, location)
    print(suggestions)