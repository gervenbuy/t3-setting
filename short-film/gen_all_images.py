import json, sys, concurrent.futures as cf
from gen_image import gen
shots = json.load(open("shots.json"))
only = set(sys.argv[1:])
todo = [s for s in shots if not only or s["id"] in only]
def run(s):
    for attempt in range(3):
        try: return gen(s["img"], f"keyframes/{s['id']}.png", use_ref=s["ref"])
        except Exception as e: err = e
    return f"FAIL {s['id']}: {err}"
with cf.ThreadPoolExecutor(6) as ex:
    for r in ex.map(run, todo): print(r)
