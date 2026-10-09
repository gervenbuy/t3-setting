"""Animate each keyframe with Veo 3.1 (image-to-video, with native audio)."""
import base64, json, os, sys, time, urllib.request, concurrent.futures as cf
MODEL = os.environ.get("VEO_MODEL", "veo-3.1-fast-generate-preview")
BASE = "https://generativelanguage.googleapis.com/v1beta"

def call(url, body=None):
    req = urllib.request.Request(url, data=json.dumps(body).encode() if body else None,
                                 headers={"Content-Type": "application/json"})
    return json.load(urllib.request.urlopen(req, timeout=300))

def gen(shot):
    img = base64.b64encode(open(f"keyframes/{shot['id']}.png", "rb").read()).decode()
    body = {"instances": [{"prompt": shot["vid"] + " Cinematic, photorealistic, consistent with the start frame. No subtitles, no on-screen text.",
                           "image": {"bytesBase64Encoded": img, "mimeType": "image/jpeg"}}],
            "parameters": {"aspectRatio": "16:9", "durationSeconds": shot["dur"], "resolution": "720p",
                           "personGeneration": "allow_adult"}}
    op = call(f"{BASE}/models/{MODEL}:predictLongRunning", body)
    while not op.get("done"):
        time.sleep(15)
        op = call(f"{BASE}/{op['name']}")
    if "error" in op: raise RuntimeError(op["error"])
    resp = op["response"]["generateVideoResponse"]
    if not resp.get("generatedSamples"): raise RuntimeError(json.dumps(resp)[:500])
    uri = resp["generatedSamples"][0]["video"]["uri"]
    out = f"clips/{shot['id']}.mp4"
    urllib.request.urlretrieve(uri if "alt=media" in uri else uri + ("&" if "?" in uri else "?") + "alt=media", out)
    return out

def run(shot):
    err = None
    for i in range(10):
        try: return gen(shot)
        except Exception as e:
            err = e; print("retry", shot["id"], str(e)[:300], flush=True)
            time.sleep(60 if "429" in str(e) else 5)
    return f"FAIL {shot['id']}: {err}"

if __name__ == "__main__":
    shots = json.load(open("shots.json"))
    only = set(sys.argv[1:])
    todo = [s for s in shots if (not only or s["id"] in only) and not os.path.exists(f"clips/{s['id']}.mp4")]
    with cf.ThreadPoolExecutor(2) as ex:
        for r in ex.map(run, todo): print(r, flush=True)
