import os
import anthropic
from dotenv import load_dotenv

load_dotenv()

key = os.environ.get("ANTHROPIC_API_KEY")
if not key:
    print("Error: ANTHROPIC_API_KEY is not set in the environment or .env file.")
    exit(1)

print(f"Testing key starting with {key[:15]} and ending with {key[-15:]}")

models_to_test = [
    "claude-3-5-sonnet-latest",
    "claude-3-5-sonnet-20241022",
    "claude-3-5-sonnet-20240620",
    "claude-3-5-haiku-20241022",
    "claude-3-haiku-20240307"
]

client = anthropic.Anthropic(api_key=key)

for model in models_to_test:
    print(f"\nTrying model: {model}...")
    try:
        response = client.messages.create(
            model=model,
            max_tokens=10,
            messages=[{"role": "user", "content": "Hello"}]
        )
        print(f"SUCCESS with {model}! Response: {response.content[0].text}")
    except Exception as e:
        print(f"FAILED with {model}: {e}")
