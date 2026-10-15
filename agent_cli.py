import glob
import os
import queue
import site
import time


def add_nvidia_dll_dirs():
    for base in site.getsitepackages():
        for path in glob.glob(os.path.join(base, "nvidia", "*", "bin")):
            os.add_dll_directory(path)
            os.environ["PATH"] = path + os.pathsep + os.environ["PATH"]


add_nvidia_dll_dirs()

import numpy as np
import requests
import sounddevice as sd
from faster_whisper import WhisperModel
from pynput import keyboard

from tools import TOOL_SCHEMAS, run_tool

SAMPLE_RATE = 16000
INPUT_DEVICE = 1
HOTKEY = keyboard.Key.f9
MIN_SECONDS = 0.4
OLLAMA_URL = "http://localhost:11434/api/chat"
OLLAMA_MODEL = "qwen3:8b"
MAX_HISTORY = 20
MAX_TOOL_ROUNDS = 3
SYSTEM_PROMPT = (
    "Ты голосовой помощник. Отвечай по-русски, коротко, одним-двумя предложениями. "
    "Если пользователь просит открыть программу, найти что-то в интернете или создать файл, "
    "вызови подходящий инструмент, а не рассказывай, как это сделать. "
    "В программном коде все имена функций, переменных, классов и файлов пиши "
    "только латиницей на английском языке, кириллицу в именах не используй."
)

frames = []
stream = None
recording = False
audio_queue = queue.Queue()
history = []

print("Загрузка модели распознавания...")
whisper = WhisperModel(
    "small",
    device="cuda",
    compute_type="float16",
    download_root="D:\\voice-agent\\models",
)
print("Модель загружена.")


def audio_callback(indata, frame_count, time_info, status):
    frames.append(indata.copy())


def start_recording():
    global stream, recording
    frames.clear()
    try:
        stream = sd.InputStream(
            samplerate=SAMPLE_RATE,
            channels=1,
            dtype="int16",
            device=INPUT_DEVICE,
            callback=audio_callback,
        )
        stream.start()
        recording = True
        print("Запись... (отпустите F9, когда закончите)")
    except Exception as error:
        print(f"Не удалось начать запись: {error}")
        stream = None
        recording = False


def stop_recording():
    global stream, recording
    recording = False
    if stream is not None:
        stream.stop()
        stream.close()
        stream = None
    if frames:
        audio_queue.put(np.concatenate(frames))


def on_press(key):
    if key == HOTKEY and not recording:
        start_recording()


def on_release(key):
    if key == HOTKEY and recording:
        stop_recording()


def transcribe(audio):
    samples = audio.flatten().astype(np.float32) / 32768.0
    segments, info = whisper.transcribe(
        samples,
        language="ru",
        beam_size=5,
        vad_filter=True,
    )
    return " ".join(segment.text.strip() for segment in segments).strip()


def recent_messages():
    window = history[-MAX_HISTORY:]
    while window and window[0]["role"] != "user":
        window = window[1:]
    return window


def ask_llm(text):
    history.append({"role": "user", "content": text})
    for _ in range(MAX_TOOL_ROUNDS):
        messages = [{"role": "system", "content": SYSTEM_PROMPT}] + recent_messages()
        payload = {
            "model": OLLAMA_MODEL,
            "messages": messages,
            "tools": TOOL_SCHEMAS,
            "think": False,
            "stream": False,
        }
        response = requests.post(OLLAMA_URL, json=payload, timeout=120)
        response.raise_for_status()
        message = response.json()["message"]
        tool_calls = message.get("tool_calls") or []
        if not tool_calls:
            answer = (message.get("content") or "").strip()
            history.append({"role": "assistant", "content": answer})
            return answer
        history.append(
            {
                "role": "assistant",
                "content": message.get("content") or "",
                "tool_calls": tool_calls,
            }
        )
        for call in tool_calls:
            function = call["function"]
            name = function["name"]
            arguments = function.get("arguments", {})
            print(f"[инструмент] {name} {arguments}")
            result = run_tool(name, arguments)
            print(f"[результат] {result}")
            history.append({"role": "tool", "tool_name": name, "content": result})
    return "Не удалось завершить действие."


def process(audio):
    duration = len(audio) / SAMPLE_RATE
    if duration < MIN_SECONDS:
        print("Запись слишком короткая, пропускаю.")
        return
    start = time.time()
    text = transcribe(audio)
    stt_time = time.time() - start
    if not text:
        print("Речь не распознана.")
        return
    print(f"Вы ({stt_time:.1f} с): {text}")
    start = time.time()
    try:
        answer = ask_llm(text)
    except Exception as error:
        print(f"Ошибка запроса к Ollama: {error}")
        return
    print(f"Агент ({time.time() - start:.1f} с): {answer}")


listener = keyboard.Listener(on_press=on_press, on_release=on_release)
listener.start()

print("Готово. Зажмите F9 и говорите. Выход: Ctrl+C.")
try:
    while True:
        try:
            audio = audio_queue.get(timeout=0.5)
        except queue.Empty:
            continue
        process(audio)
except KeyboardInterrupt:
    print("Выход.")
finally:
    listener.stop()