import httpx
import os
from dotenv import load_dotenv

load_dotenv()

client = httpx.Client(http2=False)
response = client.post(
    "https://api.anthropic.com/v1/messages",
    headers={
        "x-api-key": os.getenv("API_KEY"),
        "anthropic-version": "2023-06-01",
        "content-type": "application/json"
    },
    json={
        "model": "claude-haiku-4-5",
        "max_tokens": 10,
        "messages": [{"role": "user", "content": "hi"}]
    }
)
print(response.status_code, response.text)