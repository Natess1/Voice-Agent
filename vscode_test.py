import json

import requests

TOKEN_FILE = "D:\\voice-agent\\vscode_token.txt"
URL = "http://127.0.0.1:8765/context"

without_token = requests.get(URL, timeout=5)
print("Без токена:", without_token.status_code)

with open(TOKEN_FILE, "r", encoding="utf-8") as file:
    token = file.read().strip()

response = requests.get(URL, headers={"X-Agent-Token": token}, timeout=5)
print("С токеном:", response.status_code)
print(json.dumps(response.json(), ensure_ascii=False, indent=2))