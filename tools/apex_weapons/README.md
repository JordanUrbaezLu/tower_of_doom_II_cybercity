# Apex weapon source collection

Output: `source_library/apex_r99_peacekeeper/` (ignored by git). The installed
Apex files are read-only inputs. RSX and its writable cache are copied under
this repository's `tmp/apex_weapons/`; no shared BO3 tools or other map files
are written. Python 3.14 standard library only; RSX 2.3.0 already installed
at the path configured in `extract_sources.py`.

From the repository root:

```powershell
python tools/apex_weapons/extract_sources.py inventory common
python tools/apex_weapons/extract_sources.py inventory ui
python tools/apex_weapons/extract_sources.py inventory audio
python tools/apex_weapons/extract_sources.py extract models
python tools/apex_weapons/extract_sources.py extract motion
python tools/apex_weapons/extract_sources.py extract data
python tools/apex_weapons/extract_sources.py extract data --filter energy_shotgun,viewkick_patterns,blast_patterns,springs --label extra_definitions
python tools/apex_weapons/extract_sources.py extract ui
python tools/apex_weapons/extract_sources.py extract audio
python tools/apex_weapons/extract_supplement.py
python tools/apex_weapons/extract_icons.py
python tools/apex_weapons/collect_audio_events.py
python tools/apex_weapons/extract_linked_audio.py
python tools/apex_weapons/collect_audio_events.py
python tools/apex_weapons/archive_packages.py
python tools/apex_weapons/catalog_definitions.py
python tools/apex_weapons/audit_library.py
```

The final command builds `index.html`, the complete SHA-256/format manifest,
material-to-image filename candidates, and a compact tracked summary under
`docs/apex_weapon_evidence/`. It exits nonzero for corrupt files or missing
selected models/rigs/sequences/audio sources. It reports unresolved historical
UI references separately. CAST texture links are absent in this RSX output;
the material/image sidecar is an inference, not a native shader translation.

These commands are for a fresh collection. Preserve an existing library before
a new Apex build: exports otherwise reuse paths. The standalone-material
fallback move refuses to replace an existing archive. For future versions,
recheck RSX compatibility and the v49 audio offsets before extraction.

`fetch_rsx_reference.py` downloads only pinned official source references
under `tmp/`; it is not needed when merely browsing or auditing the collection.

Format research: [RSX 2.3.0](https://github.com/r-ex/rsx/tree/2.3.0), especially
Miles event/source handling, the CLI, and texture/UI exporters. The event
reader and GUID hash carry AGPL source attribution in their headers. Full
original weapon definitions remain authoritative; JSON preserves repeated
keys as arrays and does not invent effective gameplay statistics.
