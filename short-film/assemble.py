"""Assemble 《第三天》 from generated clips, title cards, VO, ECG, score and subtitles."""
import json, os, subprocess
FONT = "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc"
W, H, FPS = 1280, 720, 24
os.makedirs("build", exist_ok=True)
SUBS = json.load(open("subs.json"))  # {shot_id: [[start, end, text], ...]} relative to shot start
GRADE = "scale=1280:720,fps=24,eq=saturation=0.88:contrast=1.04,vignette=PI/5,noise=alls=5:allf=t,format=yuv420p"
AOUT = ["-c:a", "aac", "-ar", "48000", "-ac", "2", "-b:a", "192k"]
VOUT = ["-c:v", "libx264", "-preset", "medium", "-crf", "18", "-r", str(FPS)]

def sh(cmd): subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
def dur(f): return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", f]))

def card(name, seconds, text=None, audio=None, size=64, fade=True):
    out = f"build/{name}.mp4"
    vf = "format=yuv420p"
    if text:
        vf = (f"drawtext=fontfile={FONT}:text='{text}':fontcolor=white:fontsize={size}:x=(w-tw)/2:y=(h-th)/2"
              + (f":alpha='if(lt(t,0.6),t/0.6,if(gt(t,{seconds-0.6}),({seconds}-t)/0.6,1))'" if fade else "") + ",format=yuv420p")
    a = ["-i", audio] if audio else ["-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo"]
    sh(["ffmpeg", "-y", "-f", "lavfi", "-i", f"color=black:s={W}x{H}:r={FPS}:d={seconds}", *a,
        "-vf", vf, "-af", f"apad,atrim=0:{seconds}", "-t", str(seconds), *VOUT, *AOUT, out])
    return out

def shot(sid, vo=None, vo_at=0.0, duck=0.35):
    src, out = f"clips/{sid}.mp4", f"build/{sid}.mp4"
    if vo:
        af = (f"[0:a]volume={duck}[a0];[1:a]adelay={int(vo_at*1000)}|{int(vo_at*1000)},volume=1.6,aformat=channel_layouts=stereo[a1];"
              "[a0][a1]amix=inputs=2:duration=first:normalize=0[a]")
        sh(["ffmpeg", "-y", "-i", src, "-i", vo, "-filter_complex", f"[0:v]{GRADE}[v];{af}", "-map", "[v]", "-map", "[a]", *VOUT, *AOUT, out])
    else:
        sh(["ffmpeg", "-y", "-i", src, "-vf", GRADE, *VOUT, *AOUT, out])
    return out

def ts(t):
    h, r = divmod(t, 3600); m, s = divmod(r, 60)
    return f"{int(h)}:{int(m):02d}:{s:05.2f}"

if __name__ == "__main__":
    act1 = ["s02", "s03", "s04", "s05", "s06", "s07", "s08"]
    act2 = ["s09", "s10a", "s10b", "s11", "s12", "s13", "s14", "s15", "s16"]
    seq = [card("s01_black", 5.5, audio="audio/ecg_open.wav")]
    for s in act1:
        seq.append(shot(s, vo="audio/os_hands.wav", vo_at=1.2) if s == "s05" else shot(s))
    seq.append(card("card_3days", 3.0, text="三天前", size=56))
    seq += [shot(s) for s in act2]
    seq.append(card("end_black", 4.2, audio="audio/ecg_end.wav"))
    seq.append(card("title", 4.5, text="《第三天》", size=88))

    # absolute timeline for subtitles + score
    t, starts = 0.0, {}
    for f in seq:
        starts[os.path.basename(f)[:-4]] = t; t += dur(f)
    total = t
    with open("concat.txt", "w") as c:
        for f in seq: c.write(f"file '{f}'\n")
    sh(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", "concat.txt", "-c", "copy", "build/joined.mp4"])

    # ASS subtitles
    lines = []
    for sid, cues in SUBS.items():
        for a, b, text in cues:
            lines.append(f"Dialogue: 0,{ts(starts[sid]+a)},{ts(starts[sid]+b)},Sub,,0,0,0,,{text}")
    open("build/subs.ass", "w").write(f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Sub,WenQuanYi Zen Hei,34,&H00F0F0F0,&H000000FF,&H00000000,&H64000000,0,0,0,0,100,100,1,0,1,2,1,2,40,40,42,1
Style: OS,WenQuanYi Zen Hei,34,&H00C8C8C8,&H000000FF,&H00000000,&H64000000,0,1,0,0,100,100,1,0,1,2,1,2,40,40,42,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
""" + "\n".join(lines) + "\n")

    # Score: enters under the squad's advance (s11), swells through the ambush, cut at s15 (tinnitus silence)
    s_in, s_out = starts["s10b"] + 4.0, starts["s15"]
    sc = s_out - s_in
    af = (f"[1:a]atrim=0:{sc},afade=t=in:d=3,afade=t=out:st={sc-1.2}:d=1.2,volume=0.45,"
          f"adelay={int(s_in*1000)}|{int(s_in*1000)}[m];[0:a][m]amix=inputs=2:duration=first:normalize=0,alimiter=limit=0.95[a]")
    sh(["ffmpeg", "-y", "-i", "build/joined.mp4", "-i", "audio/score.mp3", "-filter_complex",
        f"[0:v]subtitles=build/subs.ass:fontsdir=/usr/share/fonts/truetype/wqy[v];{af}",
        "-map", "[v]", "-map", "[a]", *VOUT, *AOUT, "-movflags", "+faststart", "第三天_short_film.mp4"])
    print(f"done: {total:.1f}s")
