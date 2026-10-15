import glob
import os
import site
import time


def add_nvidia_dll_dirs():
    for base in site.getsitepackages():
        for path in glob.glob(os.path.join(base, "nvidia", "*", "bin")):
            os.add_dll_directory(path)
            os.environ["PATH"] = path + os.pathsep + os.environ["PATH"]


add_nvidia_dll_dirs()

from faster_whisper import WhisperModel

print("Загрузка модели на GPU...")
start = time.time()
model = WhisperModel(
    "small",
    device="cuda",
    compute_type="float16",
    download_root="D:\\voice-agent\\models",
)
print(f"Модель загружена за {time.time() - start:.1f} с")


def run():
    start = time.time()
    segments, info = model.transcribe(
        "test.wav",
        language="ru",
        beam_size=5,
        vad_filter=True,
    )
    text = " ".join(segment.text.strip() for segment in segments)
    return text, time.time() - start


text, elapsed = run()
print(f"Первый запуск: {elapsed:.2f} с")
text, elapsed = run()
print(f"Второй запуск: {elapsed:.2f} с")
print("Текст:", text)