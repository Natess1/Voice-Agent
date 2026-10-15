import time

from faster_whisper import WhisperModel

print("Загрузка модели...")
start = time.time()
model = WhisperModel(
    "small",
    device="cpu",
    compute_type="int8",
    download_root="D:\\voice-agent\\models",
)
print(f"Модель загружена за {time.time() - start:.1f} с")


def run(use_vad):
    print(f"\n=== vad_filter={use_vad} ===")
    start = time.time()
    segments, info = model.transcribe(
        "test.wav",
        language="ru",
        beam_size=5,
        vad_filter=use_vad,
    )
    for segment in segments:
        print(f"[{segment.start:.2f} - {segment.end:.2f}] {segment.text.strip()}")
    print(f"Время: {time.time() - start:.1f} с")


run(False)
run(True)