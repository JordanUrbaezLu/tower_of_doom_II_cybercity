"""Publish reviewed provenance/preview evidence; does not land any native inputs."""
import json,shutil,sys
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[3]
ART=ROOT/'art/wunderfizz';ART.mkdir(parents=True,exist_ok=True)
STAGE=ROOT/'tmp/wunderfizz/assets/engine_kit';TMP=ROOT/'tmp/wunderfizz/assets'
for src,name in [(STAGE/'manifest.json','asset_manifest.json'),(TMP/'source_inspection.json','source_inspection.json'),(TMP/'motion_bounds.json','motion_bounds.json'),(TMP/'duplicate_audit.json','duplicate_audit.json'),(TMP/'review/review.json','review/review.json'),(TMP/'studio_closed.json','review/studio_closed.json')]:
    dst=ART/name;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dst)
original=TMP/'source/_custom/_wetegg/models/t10/t10_zm_machine_wunderfizz_fxanim/t10_zm_machine_wunderfizz_fxanim.gdt'
(ART/'source').mkdir(exist_ok=True);shutil.copyfile(original,ART/'source/t10_zm_machine_wunderfizz_fxanim.original.gdt')
for name in ('off.png','on.png','activation_frame50.png','bo6_source_review.blend'):
    shutil.copyfile(TMP/'review'/name,ART/'review'/name)
for src in (TMP/'review').glob('i_*.png'):shutil.copyfile(src,ART/'review'/src.name)
proofs=sorted(TMP.glob('mcp_*.json'),key=lambda p:p.stat().st_mtime)
successful=next(p for p in reversed(proofs) if json.loads(p.read_text()).get('isError') is False and 'BO6_NATIVE_SOURCE_PREVIEW' in p.read_text())
shutil.copyfile(successful,ART/'review/mcp_execution.json')
# Blender paths still point to identical source-derived task preview copies.
# The persistent images+original sources are preserved regardless of tmp cleanup.
html='''<!doctype html><html><meta charset="utf-8"><title>Original BO6 Wunderfizz source import review</title><style>body{background:#17191d;color:#eee;font:16px system-ui;margin:32px}main{display:flex;gap:20px;flex-wrap:wrap}figure{margin:0;flex:1;min-width:300px}img{width:100%}p{max-width:1000px;line-height:1.5}a{color:#a9d6ff}</style><h1>Original BO6 Wunderfizz source import</h1><p>Original LOD0 geometry, UVs, materials and actual weighted activation pose imported through Blender MCP. The machine labels, original wear and native assets are preserved byte-for-byte. This bounded preview uses EEVEE, 1K source-derived preview textures and an approximate BRDF/alpha response. Original runtime textures are 4K. These images do not establish native visual approval.</p><main><figure><img src="off.png"><figcaption>Original unpowered model, animation frame 0</figcaption></figure><figure><img src="on.png"><figcaption>Original powered model, animation frame 0</figcaption></figure><figure><img src="activation_frame50.png"><figcaption>Original activation animation, frame 50 of 120</figcaption></figure></main><p><a href="../asset_manifest.json">Exact native source manifest</a> · <a href="review.json">Preview provenance</a> · <a href="mcp_execution.json">Actual MCP execution</a> · <a href="studio_closed.json">Only owned studio closed</a></p><p>All imported native inputs were hash-checked unchanged after review. Existing Blender PID 17140 was untouched; the owned 9912 studio was stopped before the native build. The user performs the final game, sound and animation review.</p></html>'''
(ART/'review/review.html').write_text(html,encoding='utf-8')
print('BO6_WUNDERFIZZ_EVIDENCE_PUBLISHED:',ART)
