"""Dealer crest review from actual source art, finished panorama and native-card preview."""
import html
import json
from pass_config import ROOT,REVIEW

build = REVIEW/'build.json'
status = 'Source ready; native build pending.'
if build.exists():
    proof = json.loads(build.read_text(encoding='utf-8'))
    status = 'Build evidence recorded; see the exact deployment proof below.'
parts = ['''<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Cybercity — The Dealer crest</title><style>body{background:#080a11;color:#d3d7df;font:16px/1.5 system-ui;margin:0 auto;padding:30px;max-width:1600px}h1,h2{color:#f1e9eb}p{max-width:1000px}section{display:grid;grid-template-columns:1fr 1fr;gap:16px}figure{margin:0 0 24px}img{display:block;width:100%;background:#02030a}figcaption{padding:8px;color:#aeb9c9}a{color:#df9cf6}.note{color:#aeb9c9}@media(max-width:800px){section{grid-template-columns:1fr}}</style></head><body>
<h1>The Dealer watches Cybercity</h1><p>The sign's crest now carries the Black Market dealer's dark hood, red X eyes and stitched grin. The imposing lettering, worn engineered frame and approved city remain in their accepted positions.</p>''', '<p>'+html.escape(status)+'</p>',
'''<p class="note">The native sign still starts dull and reveals bright after the first-jump crash. Blender shows the real exported card and texture with an approximate display conversion. BO3 bloom, exposure and runtime appearance remain for the user's playtest.</p>
<h2>Crest and frame</h2><section><figure><img src="../sign/v10_cyber_hero.png"><figcaption>Accepted frame and previous mechanical crest (historical source)</figcaption></figure><figure><img src="../sign/v12_dealer.png"><figcaption>Imagegen dealer edit; text and frame register at zero pixel shift</figcaption></figure></section>
<h2>Actual native card material bake</h2><section><figure><img src="../sign/v11_native_lit.png"><figcaption>Previous native sign</figcaption></figure><figure><img src="../sign/v12_native_lit.png"><figcaption>Dealer native sign; same worn-metal finish and foreground holdouts</figcaption></figure></section>
<h2>In the sky — matched preview</h2><section><figure><img src="../consistency_review/blender_after_reveal.png"><figcaption>Accepted v11 — after reveal</figcaption></figure><figure><img src="blender_after_reveal.png"><figcaption>Dealer — after reveal</figcaption></figure></section>
<h2>First-jump states</h2><section><figure><img src="blender_before_jump.png"><figcaption>Before jump: dull</figcaption></figure><figure><img src="blender_after_reveal.png"><figcaption>After crash: bright native card</figcaption></figure></section>
<h2>Preserved city and celestial detail</h2><section><figure><img src="before/consistency_ingame_reveal.png"><figcaption>Accepted v11 panorama</figcaption></figure><figure><img src="final/dealer_ingame_reveal.png"><figcaption>Dealer panorama with fixed baseline gain</figcaption></figure></section>
<p>Evidence: <a href="art_measurements.json">Source registration and feature measurements</a> · <a href="composition_audit.json">Exact city composition comparison</a> · <a href="native_card_art.json">Native material and visibility bake</a> · <a href="preview.json">Two-state preview inputs</a> · <a href="build.json">Deployment proof</a> · <a href="../../../tools/sky_dealer/README.md">Reproduction</a></p>
<p>Related: <a href="../../dealer_presence/review.html">Dealer sightings around the playable map</a> · <a href="../../../docs/dealer_identity.md">Shared Dealer identity and final-boss direction</a></p>
<p class="note">Open tools/sky_dealer/open_preview.ps1 for the correct Rendered preview with Scene World and Scene Lights. Earlier review folders are historical and remain intact.</p></body></html>''']
(REVIEW/'review.html').write_text('\n'.join(parts),encoding='utf-8')
print('DEALER REVIEW',REVIEW/'review.html')
