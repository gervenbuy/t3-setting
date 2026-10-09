"""Voice-over (Gemini TTS) and synthesized ECG beeps."""
import base64, json, urllib.request, subprocess, numpy as np, wave
BASE = "https://generativelanguage.googleapis.com/v1beta/models"

def post(model, body):
    req = urllib.request.Request(f"{BASE}/{model}:generateContent", data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    return json.load(urllib.request.urlopen(req, timeout=300))

def tts(text, out, voice="Fenrir", model="gemini-2.5-pro-preview-tts"):
    d = post(model, {"contents": [{"parts": [{"text": text}]}],
                     "generationConfig": {"responseModalities": ["AUDIO"],
                                          "speechConfig": {"voiceConfig": {"prebuiltVoiceConfig": {"voiceName": voice}}}}})
    pcm = base64.b64decode(d["candidates"][0]["content"]["parts"][0]["inlineData"]["data"])
    with wave.open(out, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(24000); w.writeframes(pcm)

def ecg(out, beats, sr=48000):
    """beats: list of (time_sec) for each beep; returns wav up to last beep + 1s."""
    n = int((max(beats) + 1.0) * sr); sig = np.zeros(n)
    t = np.arange(int(0.12 * sr)) / sr
    tone = np.sin(2 * np.pi * 1000 * t) * np.minimum(1, (0.12 - t) * 40) * np.minimum(1, t * 400) * 0.35
    for b in beats:
        i = int(b * sr); sig[i:i + len(tone)] += tone[: n - i]
    with wave.open(out, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr)
        w.writeframes((np.clip(sig, -1, 1) * 32767).astype(np.int16).tobytes())

if __name__ == "__main__":
    tts("Say in Mandarin Chinese (Taiwan accent), as a young man's dazed, breathy, trembling inner whisper, slowly: 這是……誰的手？",
        "audio/os_hands.wav")
    # Opening (shot 1, 5s of black): beeps accelerating
    beats, t, gap = [], 0.4, 1.0
    while t < 5.0: beats.append(t); t += gap; gap = max(0.28, gap * 0.8)
    ecg("audio/ecg_open.wav", beats)
    # Ending: fast beeps over black
    ecg("audio/ecg_end.wav", [0.6 + i * 0.42 for i in range(8)])
    print("ok")
