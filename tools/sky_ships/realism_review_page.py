"""Build the permanent matched fleet/asteroid material-review page from MCP renders."""
import pathlib
ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT/'art/sky_ships/review/realism'
keys=['dreadnought','hauler','gunship','fighter']+['rock_'+str(n) for n in range(1,6)]
keys+=['dreadnought_detail','hauler_detail','rock_2_detail']
cards=[]
for key in keys:
    assert (OUT/'before'/(key+'.png')).exists() and (OUT/'after'/(key+'.png')).exists(),key
    cards.append('<article><h2>'+key.replace('_',' ').title()+'</h2><div class="pair">'+''.join(
        '<figure><img loading="lazy" src="'+phase+'/'+key+'.png"><figcaption>'+label+'</figcaption></figure>'
        for phase,label in [('before','Before'),('after','Weathered material pass')])+'</div></article>')
variants=['dreadnought_b','hauler_b','gunship_b','fighter_b','rock_3_b','rock_4_b']
for key in variants: assert (OUT/'after'/(key+'.png')).exists(),key
html='''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width">
<title>Cybercity fleet — surface detail review</title><style>
body{background:#11151b;color:#e1e8ed;font:16px/1.55 system-ui,sans-serif;max-width:1450px;margin:40px auto;padding:0 24px}
h1{font-size:32px}h2{font-size:23px}a{color:#82c5fa}.note{max-width:1000px;color:#c0c8d2}article{margin:42px 0}
.pair,.variants{display:grid;grid-template-columns:1fr 1fr;gap:18px}figure{margin:0}img{width:100%;display:block;background:#080b0e}
figcaption{padding:9px;background:#1e2731}.variants{grid-template-columns:repeat(3,1fr)}
.distance{display:flex;align-items:center;gap:28px;flex-wrap:wrap}.distance img{width:45px;height:30px;object-fit:contain}
@media(max-width:700px){.pair,.variants{grid-template-columns:1fr}}
</style><h1>Fleet and asteroids: fine surface detail</h1>
<p class="note">Irregular exposed alloy on raised panel lips, fine scuffs, restrained oxidation in recesses,
weathered cargo enamel, heat-tempered machined nozzle collars, broken stone fractures and mineral inclusions. Color, normal, gloss and specular share
the same surface masks. Hull shapes, nozzles, lights, movement and emission strengths are preserved.</p>
<p class="note">Matched real Blender MCP renders use exported native maps and native gloss ranges with the
shared approximate fullspec shader. Same cameras, lighting and exposure; bloom is disabled. These establish
surface detail and coverage, not BO3 lighting, frame rate or native visual approval. The user performs the game test.</p>
<p><a href="../../sky_fleet_realism_preview.blend">Open the rendered Cybercity preview in Blender</a></p>
'''+''.join(cards)+'<h2>All alternate appearances</h2><div class="variants">'+''.join(
    '<figure><img loading="lazy" src="after/'+key+'.png"><figcaption>'+key.replace('_',' ').title()+'</figcaption></figure>'
    for key in variants)+'</div><h2>Small asteroid readability</h2><p class="note">45-pixel thumbnails: the texture detail merges into surface character while each silhouette remains readable.</p><div class="distance">'+''.join(
    '<img src="after/rock_'+str(n)+'.png" alt="Rock '+str(n)+' at distance">' for n in range(1,6))+'</div></html>'
(OUT/'index.html').write_text(html,encoding='utf-8')
print('REALISM_REVIEW_PAGE',OUT/'index.html')
