"""Matched depth-pass review; copy exact baseline previews, never edit pixels."""
import ast
import html
import json
import shutil
from pass_config import ROOT, REVIEW, sha

tree = ast.parse((ROOT/'tools/sky3d/finish_sky.py').read_text(encoding='utf-8'))
VIEWS = next(ast.literal_eval(n.value) for n in tree.body if isinstance(n, ast.Assign)
             and isinstance(n.value, ast.List) and any(isinstance(t, ast.Name) and t.id == 'VIEWS' for t in n.targets))
baseline = ROOT/'art/sky3d/dealer_review/final'
before = REVIEW/'before'
before.mkdir(parents=True, exist_ok=True)
manifest_path = REVIEW/'baseline_views.json'
files = {}
for source in sorted(baseline.glob('dealer_*.png')):
    target = before/source.name
    if not target.exists():
        shutil.copy2(source, target)
    assert sha(target) == sha(source), 'Preserved baseline preview differs: '+source.name
    files[source.relative_to(ROOT).as_posix()] = dict(preserved=target.relative_to(ROOT).as_posix(), sha256=sha(target))
manifest = dict(schema=1, basis='Exact v12 authored previews; native appearance was not user verified.', views=VIEWS, files=files)
if manifest_path.exists():
    assert json.loads(manifest_path.read_text(encoding='utf-8')) == json.loads(json.dumps(manifest)), 'Baseline preview set or view angles changed'
else:
    manifest_path.write_text(json.dumps(manifest, indent=2)+'\n', encoding='utf-8')
final_stats = REVIEW/'final/depth_stats.json'
if final_stats.exists():
    old = json.loads((before/'sky3d_stats.json').read_text(encoding='utf-8'))
    new = json.loads(final_stats.read_text(encoding='utf-8'))
    for key in ('size', 'gain', 'roll', 'mirror', 'display_mult', 'preview_gain'):
        assert old[key] == new[key], 'Matched display contract changed: '+key

def figure(relative, caption):
    escaped = html.escape(relative, quote=True)
    content = (f'<a href="{escaped}"><img loading="lazy" src="{escaped}" alt="{html.escape(caption, quote=True)}"></a>'
               if (REVIEW/relative).is_file() else '<div class="pending">Pending new render</div>')
    return '<figure>'+content+'<figcaption>'+html.escape(caption)+'</figcaption></figure>'

def pair(title, left, right):
    return '<h2>'+html.escape(title)+'</h2><section>'+figure(*left)+figure(*right)+'</section>'

status = ('Native build evidence recorded; the user verifies appearance in game.' if (REVIEW/'build.json').exists()
          else 'Source and review preparation in progress. Final render, native build and user appearance review are separate gates.')
parts = ['''<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Cybercity sky depth and distant detail</title><style>body{background:#080a11;color:#d3d7df;font:16px/1.5 system-ui;margin:0 auto;padding:30px;max-width:1800px}h1,h2{color:#f1e9eb}p{max-width:1100px}section{display:grid;grid-template-columns:1fr 1fr;gap:16px}figure{margin:0 0 24px}img{display:block;width:100%;background:#02030a}figcaption{padding:8px;color:#aeb9c9}a{color:#df9cf6}.note{color:#aeb9c9}.pending{aspect-ratio:16/9;display:grid;place-items:center;background:#11151e;color:#929daa}@media(max-width:800px){section{grid-template-columns:1fr}}</style></head><body>
<h1>Cybercity: depth and distant detail</h1><p>The accepted skyline, Dealer monument and celestial arrangement stay in place. This pass targets readable distant armor and service details, restrained depth shading and reconstruction quality at the existing native 8192-pixel limit.</p>''',
         '<p>'+html.escape(status)+'</p>',
         '<p class="note">Left: preserved v12 authored output. Right: v13 depth pass. Matched sky views use the same camera angles and fixed exposure; they show the dull panorama alone. Blender reveal views use the actual native card geometry, texture and scale with an approximate display conversion. BO3 bloom and exposure await the user. Click an image for full resolution.</p>']
parts.append(pair('After reveal - matched Blender preview', ('before/blender_after_reveal.png','Previous: lit native card'), ('blender_after_reveal.png','Depth pass: lit native card')))
parts.append(pair('Before jump - matched Blender preview', ('before/blender_before_jump.png','Previous: dull sign'), ('blender_before_jump.png','Depth pass: dull sign')))
for view, label in (('mid_city','Middle city'),('outer_city','Outer city'),('roofscape','Roofscape')):
    if (REVIEW/'crops'/('before_'+view+'.png')).is_file():
        parts.append(pair(label+' - geometry at native texel scale', ('crops/before_'+view+'.png','Previous art and reconstruction'),
                          ('crops/after_old_'+view+'.png','New art, previous reconstruction')))
        parts.append(pair(label+' - reconstruction comparison', ('crops/after_old_'+view+'.png','New art, previous reconstruction'),
                          ('crops/after_'+view+'.png','New art, candidate reconstruction')))
labels = dict(city='Close and middle city', behind='Outer city', skyline_r='Right skyline', harbour='Harbour',
              down_r='Lower city, right', down_l='Lower city, left', core='City core', station='Transit station',
              reveal='Title and skyline', reveal_cinematic='Cinematic title view', moon='Main moon',
              ruby='Red giant', brown='Cracked world', giant='Ringed giant', celestial_east='Eastern celestial detail',
              origin='Origin tower', gargantua='Gargantua', galaxy='Galaxy', tether='Tether station',
              maelstrom='Maelstrom', up='Upper sky', nadir='Below the city')
order = ['city','behind','skyline_r','harbour','down_r','down_l','core','station','reveal','reveal_cinematic']
ordered = sorted(VIEWS, key=lambda v: order.index(v[0]) if v[0] in order else len(order)+VIEWS.index(v))
for name, azimuth, elevation in ordered:
    angle = f'az {azimuth}°, elevation {elevation}°'
    parts.append(pair(labels.get(name, name), (f'before/dealer_ingame_{name}.png','Previous - '+angle),
                      (f'final/depth_ingame_{name}.png','Depth pass - '+angle)))
parts.append(pair('Native material and foreground visibility bake', ('before/v12_native_lit.png','Previous derived native card'),
                  ('../sign/v13_native_lit.png','Depth pass derived card; accepted painting remains unchanged')))
links = [('baseline.json','Preserved master/sky baseline'),('baseline_views.json','Matched view provenance'),
         ('art_measurements.json','Unchanged title art and anchors'),('composition_audit.json','Exact layout comparison'),
         ('architecture_check.json','Detail geometry audit'),('crops/review.html','Sampling crop gallery'),
         ('crops/review.json','Sampling crop review decision'),
         ('native_card_art.json','Native material/visibility bake'),('preview.json','Preview inputs'),
         ('build.json','Deployment proof'),('../../../tools/sky_depth/README.md','Reproduction')]
parts.append('<p>Evidence: '+' · '.join(f'<a href="{html.escape(path,quote=True)}">{html.escape(label)}</a>' for path,label in links if (REVIEW/path).is_file())+'</p>')
parts.append('<p class="note">Open tools/sky_depth/open_preview.ps1 for the saved After reveal scene with Rendered shading, Scene World and Scene Lights. Earlier passes remain historical.</p></body></html>')
(REVIEW/'review.html').write_text('\n'.join(parts), encoding='utf-8')
print('DEPTH REVIEW', REVIEW/'review.html')
