import os

from dotenv import load_dotenv

load_dotenv()

from google import genai

client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

models_to_test = [
    "gemini-1.5-flash",
    "gemini-1.5-pro",
    "gemini-2.5-pro",
    "gemini-1.5-pro-latest",
]

for m in models_to_test:
    print(f"Testing {m}...")
    try:
        response = client.models.generate_content(
            model=m,
            contents="hello"
        )
        print(f"✅ {m} works! Response: {response.text}")
    except Exception as e:
        print(f"❌ {m} failed: {e}")