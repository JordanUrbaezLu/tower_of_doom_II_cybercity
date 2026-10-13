"""Update review documentation to the actual detail-pass deployment state."""
import pathlib,json,datetime,re
ROOT=pathlib.Path(__file__).resolve().parents[2]
state=json.loads((ROOT/'tmp/necro_staff_build/status.json').read_text(encoding='utf-8-sig'))
ready=state['state']=='built'
status='FULL build and exact-source deployment verified; ready for user playtest.' if ready else 'Detail 3 source is ready; final FULL build/deployment audit is pending.'
if state['state']=='building':status='FULL build in progress (owned watcher PID '+str(state['pid'])+'); final deployment audit pending. Stage additional edits until this build finishes.'
header='**2026-09-27 - NECROMANCER HERO DETAIL 3.** '+status+' Actual Blender MCP: 11 bevelled recessed blade channels, layered leather grips/stitches with four new 2K maps, socket/halo fasteners, fine cranial sutures, Tier 3 ritual inlays and baked aged-bone pigmentation. Straight shaft, corrected Tier 2 mount, 34 staff clips and Soul Pulse native-ring fixes retained. 19 resident images, 12 native mesh LODs; unchanged grip/FX tags and full vertex parity verified. Review `docs/necro_staff/review.html`; reproduction `docs/necro_staff/DETAIL_3.md`. The preceding 18:27 build wrapper exited without its final audit and shared `_tod_class_kit.gsc` changed outside this art pass; archived as `tmp/necro_staff_build/iteration2` and not claimed verified. Current status `tmp/necro_staff_build/status.json`; do not mutate build inputs during an active build. User tests; no agent game launch. Native visual quality remains unverified.'
header+=' Native conversion exposed zero custom normals on Boolean-cut faces; geometric-normal fallback and an exhaustive unit-normal gate now cover all 12 LODs. Grip seams were corrected after macro review.'
for name in ['CLAUDE.md','CHANGELOG.md']:
    p=ROOT/name;s=p.read_text(encoding='utf-8-sig')
    s=re.sub(r'\*\*2026-09-27 - NECROMANCER HERO DETAIL 3\.\*\*[^\n]*\n\n','',s)
    p.write_text(header+'\n\n'+s,encoding='utf-8')
p=ROOT/'docs/necro_staff/README.md';s=p.read_text()
start=s.index('Status:');end=s.index('\n',start)
s=s[:start]+'Status: '+status+' See [detail pass 3](DETAIL_3.md) and [iteration 2 corrections](ITERATION_2.md). Only `built` in `tmp/necro_staff_build/status.json` confirms the current receipt. The 17:17 pass was visually rejected; the subsequent 18:27 attempt did not complete its wrapper audit. No agent game launch.'+s[end:]
p.write_text(s)
p=ROOT/'docs/necro_staff/review.html';s=p.read_text();s=s.replace('Necromancer / staff iteration 2','Necromancer / staff detail 3')
start=s.index('<p>');end=s.index('</p>',start)+4
s=s[:start]+'<p>Recessed blade engraving, layered stitched leather, aged bone, fine skull sutures and detailed fastenings. Straight staff and corrected skull mounting retained. <a href="DETAIL_3.md">Detail pass and source evidence</a>. '+status+' These are source previews, not in-game screenshots.</p>'+s[end:]
if '<h2>Surface detail</h2>' not in s:
    section='''<h2>Surface detail</h2><p>Close-ups of the exported bone, recessed blade channels and stitched leather. Native maps and authored geometry under neutral review lighting.</p><div class="grid"><figure><img src="../../art/necro_staff/detail_bone.png"><figcaption>Aged bone and fine cranial detail</figcaption></figure><figure><img src="../../art/necro_staff/detail_blade.png"><figcaption>Recessed forged blade channels</figcaption></figure><figure><img src="../../art/necro_staff/detail_grip.png"><figcaption>Spiral leather wrap and stitches</figcaption></figure></div>'''
    s=s.replace('<h2>Exported pose checks</h2>',section+'<h2>Exported pose checks</h2>')
p.write_text(s)
print(status)
