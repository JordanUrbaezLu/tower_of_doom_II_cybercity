"""Export the additional WAVs proven to be referenced by weapon audio events."""
import json
from extract_sources import LIBRARY, extract

if __name__ == "__main__":
    report = json.loads((LIBRARY / "evidence/audio_events.json").read_text())
    missing = report["missing_wavs"]
    # Keep each native argv comfortably below Windows' process command limit.
    for i in range(0, len(missing), 75):
        batch = missing[i:i + 75]
        if any("," in s for s in batch):
            raise ValueError("An audio source contains a filter delimiter")
        extract("audio", ",".join(batch), f"audio_dependencies_{i // 75 + 1:02}")
    print(f"Requested {len(missing)} linked audio sources; rerun collect_audio_events.py to verify.")
