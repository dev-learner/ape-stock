# grokit/connection_test.py
# NAME: Connection Test
# DESC: Verifies the xAI API key and returns a simple confirmation from Grok.
# DETAIL: Loads credentials from the .env file, sends a minimal prompt to the configured Grok model, and prints the reply. Used only to confirm that the API key is accepted and the endpoint is reachable. Makes no database changes and does not affect any other tools.
# ALLOW_DELETE: 1
# RUN: Tool11

"""
Connection Test
---------------
A minimal Grok-It! template that checks whether the xAI credentials in .env
are valid and the API is reachable.

It sends the prompt "Reply with the single word: connected" and prints
whatever Grok returns (or the error if the call fails).
"""

import os
import sys
from pathlib import Path

# Ensure project root is on the path so we can find .env
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

try:
    from dotenv import load_dotenv
    load_dotenv(ROOT / ".env")
except ImportError:
    print("ERROR: python-dotenv is not installed.")
    print("Run: pip install python-dotenv")
    sys.exit(1)

try:
    from openai import OpenAI
except ImportError:
    print("ERROR: openai package is not installed.")
    print("Run: pip install openai")
    sys.exit(1)

def main():
    api_key = os.getenv("XAI_API_KEY")
    base_url = os.getenv("XAI_BASE_URL", "https://api.x.ai/v1")
    model = os.getenv("DEFAULT_MODEL", "grok-4")

    if not api_key:
        print("ERROR: XAI_API_KEY not found in .env")
        return

    print(f"Using model: {model}")
    print(f"Endpoint:    {base_url}")
    print("Sending test prompt...\n")

    try:
        client = OpenAI(api_key=api_key, base_url=base_url)
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "user", "content": "Reply with the single word: connected"}
            ],
            max_tokens=20,
            temperature=0
        )
        reply = response.choices[0].message.content.strip()
        print("Grok replied:")
        print(reply)
        print("\nConnection test successful.")
    except Exception as e:
        print("ERROR: API call failed")
        print(str(e))

if __name__ == "__main__":
    main()