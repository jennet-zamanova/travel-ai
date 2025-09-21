import argparse
import json
import os
import re
from openai import OpenAI
from typing import Optional

try:
    import tomllib
except ImportError:
    try:
        import tomli as tomllib
    except ImportError:
        tomllib = None


def _load_secret_from_toml(key: str) -> Optional[str]:
    if tomllib is None:
        return None
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    secret_dir = os.path.join(base_dir, 'secret')
    candidates = [
        os.path.join(secret_dir, 'keys.local.toml'),
        os.path.join(secret_dir, 'keys.toml'),
        os.path.join(secret_dir, 'keys.example.toml'),
    ]
    for path in candidates:
        try:
            if not os.path.exists(path):
                continue
            with open(path, 'rb') as f:
                data = tomllib.load(f)
            secret_value = data.get('openai', {}).get(key)
            if secret_value:
                return secret_value
        except Exception:
            continue
    return None


def parse_budget(budget_str):
    """Parse budget string (e.g., '$300') into a number."""
    return float(re.sub(r'[^\d.]', '', budget_str))


def get_place_details(client, place):
    """Get estimated cost and review for a place using OpenAI."""
    prompt = f"Provide an estimated cost (in USD) and a review score (1-10) for visiting '{place}'. Return the output in JSON format with keys 'cost' and 'review_score'."
    try:
        response = client.chat.completions.create(
            model="gpt-5",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that provides travel information."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}
        )
        raw_response = response.choices[0].message.content
        details = json.loads(raw_response)
        # Basic validation and type conversion
        if 'cost' in details and 'review_score' in details:
            try:
                # Use regex to find the first number in the string
                cost_str = str(details['cost'])
                review_str = str(details['review_score'])
                
                cost_match = re.search(r'(\d+\.?\d*)', cost_str)
                review_match = re.search(r'(\d+\.?\d*)', review_str)

                if cost_match and review_match:
                    details['cost'] = float(cost_match.group(1))
                    details['review_score'] = float(review_match.group(1))
                    return details
                else:
                    print(f"Warning: Could not extract a valid number for cost or review_score for {place}. Skipping.")
                    return None
            except (ValueError, TypeError):
                print(f"Warning: Could not convert cost or review_score to a number for {place}. Skipping.")
                return None
        return None
    except Exception as e:
        print(f"An error occurred while fetching details for {place}: {e}")
        return None


def budget_agent(non_neg_places: list, neg_places: list, total_budget_str: str):
    """
    Main function for the budget agent.
    """
    total_budget = parse_budget(total_budget_str)

    # Filter places
    unique_neg_places = [place for place in list(set(neg_places)) if place not in non_neg_places]

    api_key = os.getenv('OPENAI_API_KEY') or _load_secret_from_toml('api_key')
    if not api_key or "your-api-key" in api_key:
        raise ValueError(
            "OpenAI API key not found or is a placeholder. "
            "Set OPENAI_API_KEY, or fill `secret/keys.local.toml`."
        )
    client = OpenAI(api_key=api_key)

    # Get details for non-neg places and calculate initial cost
    non_neg_places_details = []
    current_cost = 0
    for place in non_neg_places:
        details = get_place_details(client, place)
        if details:
            non_neg_places_details.append({'place': place, **details})
            current_cost += details['cost']

    remaining_budget = total_budget - current_cost

    # Get details for neg places and calculate score
    neg_places_details = []
    for place in unique_neg_places:
        details = get_place_details(client, place)
        if details and details['cost'] > 0:
            score = details['review_score'] / details['cost']
            neg_places_details.append({'place': place, **details, 'score': score})

    # Sort neg places by score (descending)
    neg_places_details.sort(key=lambda x: x['score'], reverse=True)

    # Select optimal neg places
    final_places = non_neg_places_details
    for place_details in neg_places_details:
        if current_cost + place_details['cost'] <= total_budget:
            final_places.append(place_details)
            current_cost += place_details['cost']

    output = {
        'final_places': final_places,
        'total_estimated_cost': current_cost,
        'total_budget': total_budget
    }
    
    output_path = 'budget_output.json'
    with open(output_path, 'w') as f:
        json.dump(output, f, indent=4)

    print(f"Budget analysis complete. Output saved to {output_path}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Plan a trip within a budget.")
    parser.add_argument("multiple_reels_output", help="Path to the JSON output from multiple_reels.py")
    parser.add_argument("style_agent_output", help="Path to the JSON output from style_agent.py")
    parser.add_argument("total_budget", help="Total budget for the trip (e.g., '$500').")
    
    args = parser.parse_args()

    # Load inputs
    multiple_reels_data = load_json_file(args.multiple_reels_output)
    style_agent_data = load_json_file(args.style_agent_output)

    if multiple_reels_data is None or style_agent_data is None:
        print("Error: Could not load input files. Exiting.")
        exit()

    non_neg_places = multiple_reels_data.get('non_neg_places', [])
    neg_places = style_agent_data.get('neg_places', [])

    budget_agent(non_neg_places, neg_places, args.total_budget)
