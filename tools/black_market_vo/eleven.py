"""Thin ElevenLabs REST client for the Black Market dealer voice work.

The key is read from ELEVENLABS_API_KEY in the process or Windows user environment. It is never written to disk,
never printed, never placed in a repo file. No SDK: plain urllib so the
tool runs on the system Python with nothing installed.
"""
import base64
import json
import os
import sys
import time
import urllib.error
import urllib.request

BASE = "https://api.elevenlabs.io"


def configured_key():
    """Resolve a saved user key even when the terminal inherited an older environment."""
    k = os.environ.get("ELEVENLABS_API_KEY", "").strip()
    if k:
        return k, "process environment"
    if os.name == "nt":
        import winreg
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment") as env:
                saved, _ = winreg.QueryValueEx(env, "ELEVENLABS_API_KEY")
        except OSError:
            saved = ""
        if isinstance(saved, str) and saved.strip():
            k = saved.strip()
            # Child generators need the same key. This changes only this process,
            # never the registry or a repository file.
            os.environ["ELEVENLABS_API_KEY"] = k
            return k, "Windows user environment"
    return "", None


def key():
    k, _ = configured_key()
    if not k:
        sys.exit("ELEVENLABS_API_KEY is unavailable in the process and Windows user environment")
    return k


def call(method, path, body=None, query=None, retries=3):
    url = BASE + path
    if query:
        url += "?" + "&".join(f"{k}={v}" for k, v in query.items())
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("xi-api-key", key())
    if data is not None:
        req.add_header("Content-Type", "application/json")
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=180) as r:
                ctype = r.headers.get("Content-Type", "")
                raw = r.read()
                if ctype.startswith("application/json"):
                    return json.loads(raw)
                return raw
        except urllib.error.HTTPError as e:
            msg = e.read().decode(errors="replace")
            if e.code in (429, 500, 502, 503) and attempt + 1 < retries:
                time.sleep(3 * (attempt + 1))
                continue
            raise RuntimeError(f"{method} {path} -> {e.code}: {msg[:600]}")
    raise RuntimeError("unreachable")


def design_previews(description, text, model_id="eleven_ttv_v3", guidance_scale=None, loudness=None, seed=None, quality=None):
    body = {"voice_description": description, "text": text, "model_id": model_id}
    if quality is not None:
        body["quality"] = quality
    if guidance_scale is not None:
        body["guidance_scale"] = guidance_scale
    if loudness is not None:
        body["loudness"] = loudness
    if seed is not None:
        body["seed"] = seed
    return call("POST", "/v1/text-to-voice/design", body, {"output_format": "mp3_44100_128"})


def remix_previews(voice_id, description, text, guidance_scale=None, loudness=None, seed=None):
    """Iterate an EXISTING voice from a description of the change; returns previews like design_previews."""
    body = {"voice_description": description, "text": text}
    if guidance_scale is not None:
        body["guidance_scale"] = guidance_scale
    if loudness is not None:
        body["loudness"] = loudness
    if seed is not None:
        body["seed"] = seed
    return call("POST", f"/v1/text-to-voice/{voice_id}/remix", body, {"output_format": "mp3_44100_128"})


def save_voice(name, description, generated_voice_id, labels=None):
    body = {"voice_name": name, "voice_description": description, "generated_voice_id": generated_voice_id}
    if labels:
        body["labels"] = labels
    return call("POST", "/v1/text-to-voice", body)


def tts(voice_id, text, model_id="eleven_v4", stability=None, similarity=None, style=None, speed=None, seed=None,
        output_format="pcm_48000"):
    body = {"text": text, "model_id": model_id}
    vs = {}
    if stability is not None:
        vs["stability"] = stability
    if similarity is not None:
        vs["similarity_boost"] = similarity
    if style is not None:
        vs["style"] = style
    if speed is not None:
        vs["speed"] = speed
    if vs:
        body["voice_settings"] = vs
    if seed is not None:
        body["seed"] = seed
    return call("POST", f"/v1/text-to-speech/{voice_id}", body, {"output_format": output_format})


def b64_to_file(b64, path):
    with open(path, "wb") as f:
        f.write(base64.b64decode(b64))
