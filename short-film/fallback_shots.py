"""Shots s12–s16 animated locally from keyframes (Veo quota exhausted): camera moves, flicker, synthesized SFX."""
import subprocess, wave, numpy as np
SR, FPS = 48000, 24
rng = np.random.default_rng(7)

def wav(name, sig):
    sig = np.clip(sig, -1, 1)
    with wave.open(name, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((sig * 32767).astype(np.int16).tobytes())

def lowpass(x, a):  # one-pole
    y = np.empty_like(x); acc = 0.0
    for i, v in enumerate(x): acc += a * (v - acc); y[i] = acc
    return y

def rain(sec, gain=0.12):
    return lowpass(rng.normal(0, 1, int(sec * SR)), 0.25) * gain

def boom(sec, at, gain=0.9, slow=1.0):
    out = np.zeros(int(sec * SR)); L = int(1.2 * slow * SR)
    burst = lowpass(rng.normal(0, 1, L), 0.02 / slow) * np.exp(-np.arange(L) / (0.25 * slow * SR)) * gain * 6
    for t in at:
        i = int(t * SR); out[i:i + L] += burst[: len(out) - i]
    return out

def tone(sec, f, gain, fade_in=0.5):
    t = np.arange(int(sec * SR)) / SR
    return np.sin(2 * np.pi * f * t) * gain * np.minimum(1, t / fade_in)

def static(sec, gain=0.15):
    n = rng.normal(0, 1, int(sec * SR)); crackle = (rng.random(len(n)) > 0.9985) * rng.normal(0, 3, len(n))
    hp = n - lowpass(n, 0.3)
    env = 0.6 + 0.4 * np.sin(np.arange(len(n)) / SR * 2 * np.pi * 3.1) ** 2
    return (hp * env + crackle) * gain

def render(sid, sec, vf, audio):
    wav(f"build/{sid}_fx.wav", audio)
    n = sec * FPS
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-loop", "1", "-i", f"keyframes/{sid}.png", "-i", f"build/{sid}_fx.wav",
                    "-filter_complex", f"[0:v]scale=3840:-1,{vf.format(n=n)},format=yuv420p[v]",
                    "-map", "[v]", "-map", "1:a", "-t", str(sec), "-r", str(FPS), "-c:v", "libx264", "-crf", "16",
                    "-c:a", "aac", "-ar", "48000", "-ac", "2", f"clips/{sid}.mp4"], check=True)

PUSH = "zoompan=z='1+{rate}*on':x='iw/2-(iw/zoom/2){dx}':y='ih/2-(ih/zoom/2){dy}':d={{n}}:s=1280x720:fps=24"
import subprocess as _s
if __name__ == "__main__":
    import os; os.makedirs("build", exist_ok=True)
    # s12: NVG view, slow ominous push-in, rain fading to near-silence
    a = rain(6, 0.14) * np.linspace(1, 0.35, 6 * SR)
    render("s12", 6, PUSH.format(rate=0.0007, dx="", dy="") + ",noise=alls=14:allf=t", a)
    # s13: radio close-up, nervous handheld micro-shake, static bursts + squelch
    a = rain(6, 0.06) + static(6, 0.18) + boom(6, [4.2], 0.25)
    render("s13", 6, PUSH.format(rate=0.0012, dx="+6*sin(on/3)", dy="+4*cos(on/4)"), a)
    # s14: ambush wide, slow push, muzzle-flash flicker, slowed muffled booms
    hits = sorted(rng.uniform(0.3, 7.5, 9))
    a = rain(8, 0.10) + boom(8, hits, 0.8, slow=1.6)
    flick = "+".join(f"0.22*between(t,{h:.2f},{h+0.08:.2f})" for h in hits)
    render("s14", 8, PUSH.format(rate=0.0006, dx="", dy="") + f",eq=brightness='{flick}':eval=frame", a)
    # s15: POV, everything silent but tinnitus; slow drift + dreamy blur
    a = tone(6, 4200, 0.12, 0.3) + boom(6, [0.2], 0.25, slow=2.5)
    render("s15", 6, PUSH.format(rate=0.0009, dx="+8*sin(on/20)", dy="-on*0.15") + ",gblur=sigma='1.5'", a)
    # s16: eye macro, fast push, orange flare flicker
    hits = sorted(rng.uniform(0.2, 3.6, 5))
    a = tone(4, 4200, 0.12, 0.05) + boom(4, hits, 0.35, slow=2.0)
    flick = "+".join(f"0.15*between(t,{h:.2f},{h+0.1:.2f})" for h in hits)
    render("s16", 4, PUSH.format(rate=0.0025, dx="", dy="") + f",eq=brightness='{flick}':eval=frame", a)
    print("ok")
