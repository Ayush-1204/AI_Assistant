import os

import requests
from dotenv import load_dotenv

load_dotenv()
api_key = os.environ.get("GEMINI_API_KEY")

if not api_key:
    print("NO API KEY FOUND")
    exit(1)

model = "gemini-1.5-flash"
url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"

payload = {
    "contents": [{"parts": [{"text": "Hello, how are you?"}]}]
}
headers = {'Content-Type': 'application/json'}

response = requests.post(url, json=payload, headers=headers)
print(f"Status: {response.status_code}")
print(f"Response: {response.text}")
