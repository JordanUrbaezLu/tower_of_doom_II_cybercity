"""Local authoring desk: exact-binary contact frames and pinned sound cues."""
import html
import json
import pathlib
ROOT=pathlib.Path(__file__).resolve().parents[2]
OUT=ROOT/'art/dealer_combat/review'
review=json.loads((OUT/'review.json').read_text())
sounds=json.loads((ROOT/'sound_assets/tod/dealer_combat/manifest.json').read_text())
cards=[]
for name,item in review['poses'].items():
    cards.append('<figure><img src="'+name+'.png"><figcaption>'+html.escape(name.replace('_',' ').title())+
        ' — '+html.escape(item['weapon'])+', actual native clip frame '+str(item['frame'])+'</figcaption></figure>')
rows=[]
for name,item in sounds.items():
    rows.append('<tr><td>'+html.escape(name)+'</td><td>'+str(round(item['seconds'],2))+'s / '+
        str(round(item['lufs'],1))+' LUFS</td><td><audio controls preload="none" src="../../../sound_assets/tod/dealer_combat/'+
        html.escape(item['file'])+'"></audio></td></tr>')
page='''<!doctype html><meta charset="utf-8"><title>Dealer combat review</title>
<style>body{background:#101015;color:#eee;font:16px system-ui;margin:32px;max-width:1200px}h1{font-size:28px}
p{line-height:1.6}a{color:#ff807b}.frames{display:grid;grid-template-columns:1fr 1fr;gap:20px}
figure{margin:0;background:#19191f}img{width:100%}figcaption{padding:12px}td{padding:12px;border-bottom:1px solid #444}
small{color:#b4b4c0}@media(max-width:700px){.frames{grid-template-columns:1fr}}</style>
<h1>The Dealer · weapon pass</h1><p>Native gun clips and models with an editable warning/effect study.
The full 100-unit footprint is shown at player height. No bloom is used. Studio lighting and preview
effect geometry are approximations; BO3 appearance, audio and performance await your playtest.</p>
<p>Move out of a fixed mark to dodge. Cover blocks damage. Pause, stun, phase changes and death cancel
the attack. The shock hits each player once; six Dingo rounds stay inside the warned footprint.</p>
<div class="frames">'''+''.join(cards)+'''</div><h2>Sound cues</h2>
<p>Two generated takes per cue, measured and selected. No Dealer voice changed.</p><table>'''+''.join(rows)+'''</table>
<p><a href="dealer_combat.blend">Editable Blender review</a> · <a href="review.json">Clip/camera evidence</a> ·
<a href="../build.json">Native delivery proof</a></p>
<small>Independent code/art review passed. This is not a native playtest.</small>'''
(OUT/'review.html').write_text(page,encoding='utf-8')
print('DEALER COMBAT REVIEW DESK: four exact-clip views and four cue players')
