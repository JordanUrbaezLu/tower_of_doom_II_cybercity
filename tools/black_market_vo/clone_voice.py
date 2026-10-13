"""THE CLONE (user 2026-10-01: written permission from Nolan North and from Activision, custom-map only, non-commercial).

The user supplied the permission text and explicitly removed the filename-based gate on 2026-10-01.
Permission files are recorded as provenance, without blocking on their names. The custom-map-only,
non-commercial terms remain in the saved voice's description so they travel with it.

  python tools/black_market_vo/clone_voice.py            instant clone from tmp/black_market_vo/clone_source (clone_prep.py first)
  python tools/black_market_vo/clone_voice.py --check    check source files + key without an API request

Needs: the ElevenLabs key with "Voices: write". The key is resolved from the process or saved Windows user environment;
its value is never printed. Local --check does not verify remote key scopes. On success the voice id is written to
tmp/black_market_vo/unmasked/voices.json under "clone" and
the organic reveal lines (lines_reveal_organic.json) are generated through it into tmp/black_market_vo/unmasked/clone/
for the desk (build_desk.py --full clone --alt V2).
"""
import argparse
import glob
import json
import os
import subprocess
import sys
import urllib.error
import urllib.request
import uuid

sys.path.insert(0, os.path.dirname(__file__))
import eleven  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
VO = os.path.join(ROOT, "tmp", "black_market_vo")
SRC = os.path.join(VO, "clone_source")
LIC = os.path.join(ROOT, "docs", "licenses")
VOICE_NAME = "TOD2 Richtofen (consented clone)"
TERMS = ("Voice clone of Edward Richtofen as performed by Nolan North, made with written permission from Nolan North and "
         "Activision for the Tower of Doom II: Cybercity custom map ONLY, non-commercial: never for money, never outside "
         "that map. Permissions on file in the map repository under docs/licenses/.")


def permissions():
    files = [f for f in glob.glob(os.path.join(LIC, "*")) if os.path.isfile(f)]
    north = [f for f in files if "north" in os.path.basename(f).lower()]
    acti = [f for f in files if "activision" in os.path.basename(f).lower()]
    return north, acti


def source_files():
    man = os.path.join(SRC, "manifest.json")
    if not os.path.exists(man):
        return [], 0.0
    m = json.load(open(man, encoding="utf-8"))
    # The instant-clone endpoint accepts at most 25 samples. Keep the
    # longest approved lines, without altering the prepared source pool.
    rows = sorted((r for r in m["files"] if not r.get("skipped")),
                  key=lambda r: (-r["seconds"], r["file"]))[:25]
    files = [os.path.join(SRC, r["file"]) for r in rows]
    return files, sum(r["seconds"] for r in rows)


def multipart(fields, files):
    boundary = "----tod2" + uuid.uuid4().hex
    body = b""
    for k, v in fields.items():
        body += ("--%s\r\nContent-Disposition: form-data; name=\"%s\"\r\n\r\n%s\r\n" % (boundary, k, v)).encode("utf-8")
    for path in files:
        body += ("--%s\r\nContent-Disposition: form-data; name=\"files\"; filename=\"%s\"\r\nContent-Type: audio/wav\r\n\r\n"
                 % (boundary, os.path.basename(path))).encode("utf-8")
        body += open(path, "rb").read() + b"\r\n"
    body += ("--%s--\r\n" % boundary).encode("utf-8")
    return boundary, body


def add_voice(files):
    boundary, body = multipart({"name": VOICE_NAME, "description": TERMS, "remove_background_noise": "true",
                                "labels": json.dumps({"map": "tod2", "role": "richtofen_consented_clone", "use": "custom_map_only_noncommercial"})},
                               files)
    req = urllib.request.Request(eleven.BASE + "/v1/voices/add", data=body, method="POST")
    api_key = eleven.key()
    req.add_header("xi-api-key", api_key)
    req.add_header("Content-Type", "multipart/form-data; boundary=" + boundary)
    try:
        with urllib.request.urlopen(req, timeout=300) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as error:
        message = error.read().decode("utf-8", errors="replace")
        try:
            detail = json.loads(message).get("detail", message)
            if isinstance(detail, dict):
                message = "%s: %s" % (detail.get("status", "request_failed"), detail.get("message", detail))
            else:
                message = str(detail)
        except (ValueError, AttributeError):
            pass
        message = (message or str(error.reason)).replace(api_key, "[redacted]")
        sys.exit("ElevenLabs voice creation failed (HTTP %s): %s" % (error.code, message[:800]))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    north, acti = permissions()
    files, total = source_files()
    print("permission records: North %s, Activision %s" % (north or "no named record", acti or "no named record"))
    print("clone source: %d files, %.1f s" % (len(files), total))
    api_key, key_source = eleven.configured_key()
    print("key:", "set (%s)" % key_source if api_key else "MISSING (process and Windows user environment)")
    if a.check:
        problems = []
        if not files:
            problems.append("clone source missing")
        elif any(not os.path.isfile(path) or os.path.getsize(path) == 0 for path in files):
            problems.append("clone source files missing or empty")
        if total < 60:
            problems.append("clone source under 60 s")
        if not api_key:
            problems.append("API key unavailable")
        if problems:
            sys.exit("CHECK FAILED: " + "; ".join(problems) + ". Nothing was sent.")
        print("CHECK PASS: source files and key available; Voices: write remains an API-side requirement")
        return
    if not files:
        sys.exit("no clone source: run clone_prep.py first")
    if total < 60:
        sys.exit("clone source under 60 s; an instant clone wants 1-5 minutes")
    resp = add_voice(files)
    vid = resp.get("voice_id")
    if not vid:
        sys.exit("no voice_id in the response: %s" % json.dumps(resp)[:400])
    vpath = os.path.join(VO, "unmasked", "voices.json")
    voices = json.load(open(vpath)) if os.path.exists(vpath) else {}
    voices["clone"] = {"voice_id": vid, "name": VOICE_NAME, "terms": TERMS, "source_files": [os.path.basename(f) for f in files],
                       "source_seconds": total, "permissions": {"north": [os.path.relpath(p, ROOT) for p in north],
                                                                 "activision": [os.path.relpath(p, ROOT) for p in acti]}}
    json.dump(voices, open(vpath, "w", encoding="utf-8"), indent=2)
    print("CLONED:", vid, "->", vpath)
    # the organic reveal lines through it, for the desk
    out = os.path.join(VO, "unmasked", "clone")
    subprocess.run([sys.executable, os.path.join(os.path.dirname(__file__), "generate.py"), "--lines",
                    os.path.join(os.path.dirname(__file__), "lines_reveal_organic.json"), "--voice", vid, "--out", out, "--takes", "2"], check=True)
    print("reveal lines:", out, "- next: build_desk.py --masked V2mask --full clone --alt V2")


if __name__ == "__main__":
    main()
