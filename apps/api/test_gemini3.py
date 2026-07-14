import os

import requests
from dotenv import load_dotenv

load_dotenv()
api_key = os.environ.get("GEMINI_API_KEY")

url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
try:
    response = requests.get(url)
    models = response.json().get("models", [])
    valid_names = [m["name"].replace("models/", "") for m in models]
    print("Valid models:")
    for v in valid_names:
        if "gemini" in v.lower():
            print(f"- {v}")
except Exception as e:
    print(f"Failed to list models: {e}")
