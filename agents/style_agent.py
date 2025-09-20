import os
import json
try:
    import tomllib  # Python 3.11+
except ImportError:
    tomllib = None
from typing import Optional, List, Dict, Any
from openai import OpenAI


class StyleAgent:
    """
    Travel Style Agent that generates personalized place recommendations
    based on city and style preferences using OpenAI's GPT API.
    Returns a JSON string with a specific schema.
    """

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        """
        Initializes the StyleAgent.
        - Loads API key from parameter, environment variable, or secret/keys.local.toml.
        - Loads model from parameter, environment variable, or secret/keys.local.toml.
        """
        # API Key Loading
        if api_key:
            resolved_api_key = api_key
        else:
            resolved_api_key = os.getenv('OPENAI_API_KEY') or self._load_secret_from_toml('api_key')

        if not resolved_api_key or "your-api-key" in resolved_api_key:
            raise ValueError(
                "OpenAI API key not found or is a placeholder. "
                "Provide api_key, set OPENAI_API_KEY, or fill `secret/keys.local.toml`."
            )
        self.client = OpenAI(api_key=resolved_api_key)

        # Model loading
        if model:
            self.model = model
        else:
            self.model = self._load_secret_from_toml('model') or "gpt-5"

    def _load_secret_from_toml(self, key: str) -> Optional[str]:
        """
        Loads a secret value (like 'api_key' or 'model') from TOML files.
        Priority: keys.local.toml -> keys.toml -> keys.example.toml.
        """
        if tomllib is None:
            return None

        # Correctly locate the project's base directory to find the 'secret' folder
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

    def _create_prompt(self, city: str, style: str) -> str:
        """Creates a prompt that instructs the model to return a specific JSON schema."""
        return f"""You are a helpful travel expert who provides structured data.
A user wants a list of 10-15 {style} places to visit in {city}.

Your response must be a single, valid JSON object and nothing else.
The JSON must strictly follow this schema:
{{
  "places": "string",
  "locations": ["string", ...]
}}

Instructions:
1.  In the "places" field, provide a single string containing the names of the recommended places, separated by a newline character (\\n).
2.  In the "locations" field, provide a JSON array of strings, where each string is the address or area for the corresponding place.
3.  Ensure the number of locations in the array matches the number of places in the "places" string.
4.  Do not include any text, explanations, or markdown formatting before or after the JSON object.

Generate the JSON for {style} places in {city} now."""

    def _parse_and_validate_json(self, json_string: str) -> Dict[str, Any]:
        """
        Parses a JSON string and validates it against the required schema.
        
        Returns:
            A dictionary if the JSON is valid.
        
        Raises:
            ValueError: If the JSON is invalid or does not match the schema.
        """
        try:
            # Clean the string to remove potential markdown code blocks
            if json_string.startswith("```json"):
                json_string = json_string[7:].strip()
            if json_string.endswith("```"):
                json_string = json_string[:-3].strip()

            data = json.loads(json_string)
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to decode JSON from the model's response. Error: {e}")

        # Schema validation
        if not isinstance(data, dict):
            raise ValueError("Invalid response: The root of the response is not a JSON object.")
        
        if "places" not in data or not isinstance(data["places"], str):
            raise ValueError("Invalid schema: The 'places' key is missing or is not a string.")
            
        if "locations" not in data or not isinstance(data["locations"], list):
            raise ValueError("Invalid schema: The 'locations' key is missing or is not a list.")

        if not all(isinstance(loc, str) for loc in data["locations"]):
            raise ValueError("Invalid schema: Not all items in the 'locations' list are strings.")

        # Cross-validation: Ensure counts match
        place_names = data["places"].strip().split('\n')
        if len(place_names) != len(data["locations"]):
            raise ValueError("Data mismatch: The number of places does not match the number of locations.")

        return data

    def get_recommendations(self, city: str, style: str) -> str:
        """
        The main method to get travel recommendations as a JSON string.

        Args:
            city: The destination city (e.g., "Paris").
            style: The travel style (e.g., "aesthetic").

        Returns:
            A single, validated JSON string conforming to the specified schema.
        """
        if not city or not isinstance(city, str):
            raise ValueError("City must be a non-empty string.")
        if not style or not isinstance(style, str):
            raise ValueError("Style must be a non-empty string.")

        city = city.strip()
        style = style.strip().lower()

        try:
            prompt = self._create_prompt(city, style)

            request_kwargs = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": "You are a helpful API that returns structured JSON data according to the user's schema."},
                    {"role": "user", "content": prompt}
                ],
            }
            if self.model != "gpt-5":
                request_kwargs["temperature"] = 0.5 # Lower temperature for more predictable JSON
            
            response_obj = self.client.chat.completions.create(**request_kwargs)
            choice = response_obj.choices[0]
            response_text = choice.message.content

            if choice.finish_reason == 'content_filter':
                raise ValueError("The request was blocked by OpenAI's content filter.")

            if not response_text:
                raise ValueError(f"GPT returned an empty response. Finish reason: '{choice.finish_reason}'.")

            # Parse and validate the JSON
            validated_data = self._parse_and_validate_json(response_text)

            # Re-serialize to ensure clean, valid JSON output
            return json.dumps(validated_data, indent=2)

        except Exception as e:
            raise Exception(f"Failed to get recommendations: {e}")


if __name__ == "__main__":
    """A simple test when running the script directly."""
    try:
        print("--- Running StyleAgent Self-Test (JSON Mode) ---")
        agent = StyleAgent()
        city = "Tokyo"
        style = "foodie"
        print(f"Getting {style} recommendations for {city}...\n")
        
        json_output = agent.get_recommendations(city, style)
        
        print("--- Raw JSON Output ---")
        print(json_output)
        print("-----------------------")

        # Demonstrate parsing the output
        data = json.loads(json_output)
        places = data['places'].split('\n')
        locations = data['locations']
        print("\n--- Parsed Data ---")
        for place, location in zip(places, locations):
            print(f"- {place}: {location}")
        print("-------------------")
        
        print("\n✅ Self-test completed successfully.")

    except Exception as e:
        print(f"\n❌ Error during self-test: {e}")
        print("Please ensure your `secret/keys.local.toml` is configured correctly.")
