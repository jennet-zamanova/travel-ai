# Travel AI

Travel AI is a Python-based project that uses AI agents to help you plan your trips. It can provide travel recommendations based on your style and create a budget for your trip.

## Features

- **Style-based Recommendations**: Get recommendations for places to visit in a city based on a specific style (e.g., romantic, adventurous).
- **Budget Planning**: Generate a budget for a list of places to visit.
- **Video Reel Processing**: (Work in progress) Process a collection of video reels to create a travel video.

## Getting Started

### Prerequisites

- Python 3.8+
- An OpenAI API key

### Installation

1. **Clone the repository:**

   ```bash
   git clone https://github.com/your-username/travel-ai.git
   cd travel-ai
   ```

2. **Install the dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

### Configuration

1. **Set up your OpenAI API key:**

   Run the setup script and follow the prompts:

   ```bash
   python setup_openai.py
   ```

   This will create a `secret/keys.local.toml` file with your API key.

## Usage

### Style Agent Example

The `StyleAgent` provides recommendations for a city based on a given style.

To run the example:

```bash
python example_usage.py
```

This will get "romantic" recommendations for "London" and print the JSON response.

### Budget Agent Example

The `budget_agent` creates a budget for a list of places.

To run the example:

```bash
python example_budget.py
```

This will generate a budget for a predefined list of places and save it to `budget_output.json`.

### Web Application

The project also includes a simple web interface built with Streamlit.

To run the web app:

```bash
streamlit run main.py
```

This will start a local web server and open the application in your browser. The web interface allows you to upload a collection of reels for processing (note: this feature is still under development).

## Agents

- **`StyleAgent`**: Takes a city and a style as input and returns a JSON object with recommended places and locations.
- **`budget_agent`**: Takes a list of places and a total budget and returns a detailed budget plan in JSON format.
- **`multiple_reels`**: (Work in progress) Processes multiple video reels.
- **`process_video`**: (Work in progress) Processes a single video.