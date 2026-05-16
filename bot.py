from validator import validate_response
from constants import modes, buckets, priorities, keys, PROMPT, kills, RETRY_PROMPT
import os
from dotenv import load_dotenv
import logging
import json
import httpx

load_dotenv()
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(name)s %(levelname)s %(message)s')
logger = logging.getLogger(__name__)


def call_api(user_input: str) -> object:
    try:
        client = httpx.Client(http2=False, timeout=30)
        response = client.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": os.getenv("API_KEY"),
                "anthropic-version": "2023-06-01",
                "content-type": "application/json"
            },
            json={
                'system': PROMPT,
                "model": "claude-haiku-4-5",
                "max_tokens": 1024,
                "messages": [{"role": "user", "content": user_input}]
            }
        )
        logger.info(f"API call successful, status {response.status_code}")
        return response
    except Exception as e:
        logger.error(f"API call failed: {type(e).__name__}: {e}")
        raise


def parse_response(response) -> list:
    rep = response.json()['content'][0]['text']
    rep = rep.replace("```json", "")
    rep = rep.replace("```", "")
    rep = rep.strip()
    rep = json.loads(rep)
    return rep


def run():
    r = True
    while r:
        user_input = str(input("What's good?  "))
        logger.info(f"Received input: {user_input[:50]}")
        for kill in kills:
            if kill in user_input.lower():
                logger.info("Kill phrase detected, shutting down")
                r = False
                break
        if not r:
            continue
        counter = 0
        error = None
        while counter < 5:
            if counter == 0:
                response = call_api(user_input)
            else:
                ret_input = RETRY_PROMPT + error + user_input
                logger.warning(f"Retrying attempt {counter + 1}: {error}")
                response = call_api(ret_input)
            response = parse_response(response)
            error = validate_response(response)
            if error:
                counter += 1
                continue
            else:
                logger.info(f"Valid response received after {counter + 1} attempt(s)")
                break
        else:
            logger.error(f"All 5 attempts failed. Last error: {error}")
            print("Input error — please try again.")
            continue
        for item in response:
            if item['mode'] == 'interactive':
                print(f"\nAssistant: {item['response']}\n")
            elif item['mode'] == 'task':
                print(f"\nTask: {item['task']} | Bucket: {item['bucket']} | Priority: {item['priority']} | Due: {item['date']}\n")


if __name__ == "__main__":
    run()