import wave

import numpy as np
import sounddevice as sd

SAMPLE_RATE = 16000
SECONDS = 5

print(sd.query_devices())

choice = input("Номер устройства ввода (Enter - по умолчанию): ").strip()
device = int(choice) if choice else None

print(f"Говорите {SECONDS} секунд...")
audio = sd.rec(
    int(SECONDS * SAMPLE_RATE),
    samplerate=SAMPLE_RATE,
    channels=1,
    dtype="int16",
    device=device,
)
sd.wait()

peak = int(np.abs(audio).max())
print(f"Пиковая громкость: {peak} из 32767")

with wave.open("test.wav", "wb") as f:
    f.setnchannels(1)
    f.setsampwidth(2)
    f.setframerate(SAMPLE_RATE)
    f.writeframes(audio.tobytes())

print("Воспроизведение...")
sd.play(audio, SAMPLE_RATE)
sd.wait()
print("Готово, запись сохранена в test.wav")

print("hello")