import time

import requests

URL = "http://localhost:11434/api/chat"
MODEL = "qwen3:8b"

payload = {
    "model": MODEL,
    "messages": [
        {
            "role": "system",
            "content": "Ты голосовой помощник. Отвечай по-русски, коротко, одним-двумя предложениями.",
        },
        {
            "role": "user",
            "content": "Привет! Как тебя зовут и что ты умеешь?",
        },
    ],
    "think": False,
    "stream": False,
}

start = time.time()
response = requests.post(URL, json=payload, timeout=120)
response.raise_for_status()
data = response.json()
elapsed = time.time() - start

message = data["message"]
print(f"Время: {elapsed:.1f} с")
print("Рассуждения:", repr(message.get("thinking")))
print("Ответ:", message["content"])