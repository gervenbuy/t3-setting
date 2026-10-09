"""Generate a 16:9 keyframe with Gemini image model, using the character sheet as reference."""
import base64, json, sys, urllib.request, os
MODEL = os.environ.get("IMG_MODEL", "gemini-3-pro-image")
API = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent"
HERE = os.path.dirname(os.path.abspath(__file__))
REF = os.path.join(HERE, "character_sheet_07.png")

STYLE = ("Rendered in the same semi-realistic painterly-photoreal style as the reference sheet (realistic skin texture, realistic lighting) — NOT anime, NOT cel-shaded, NOT cartoon. Cinematic film still, anamorphic 2.39-feel framed in 16:9, moody desaturated "
         "palette of charcoal, olive and cold grey with pale skin tones, heavy film grain, shallow depth of field. "
         "No text, no captions, no watermark, no UI.")

def gen(prompt, out, use_ref=True):
    parts = []
    if use_ref:
        parts.append({"inline_data": {"mime_type": "image/png", "data": base64.b64encode(open(REF, "rb").read()).decode()}})
        parts.append({"text": "Reference: character design sheet for the protagonist '07' (an 18-19 year old East Asian young man, "
                              "messy black hair falling over the eyes, dark grey eyes, lean build, dirty olive-black tactical uniform). "
                              "Keep his face and hair consistent with this sheet. Do NOT reproduce the sheet layout or any text from it."})
    parts.append({"text": prompt + "\n\n" + STYLE})
    body = {"contents": [{"parts": parts}],
            "generationConfig": {"responseModalities": ["IMAGE"], "imageConfig": {"aspectRatio": "16:9"}}}
    req = urllib.request.Request(API, data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
    d = json.load(urllib.request.urlopen(req, timeout=300))
    for p in d["candidates"][0]["content"]["parts"]:
        if "inlineData" in p:
            open(out, "wb").write(base64.b64decode(p["inlineData"]["data"]))
            return out
    raise RuntimeError(json.dumps(d)[:800])

if __name__ == "__main__":
    print(gen(sys.argv[1], sys.argv[2], use_ref=(len(sys.argv) < 4 or sys.argv[3] != "noref")))
