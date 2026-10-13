"""Build a local matched-view gallery from existing, unmodified preview images."""
import argparse
import datetime
import html
import json
import pathlib

from pass_config import ROOT, REVIEW, sha

VIEWS = (
    ('city', 'Near and middle city'),
    ('skyline_r', 'Distant skyline'),
    ('reveal_cinematic', 'Title at the cinematic view'),
    ('station', 'Skyrail station'),
    ('moon', 'Primary moon'),
    ('celestial_east', 'Celestial east'),
    ('ruby', 'Red giant'),
    ('brown', 'Cracked world'),
    ('giant', 'Ringed giant'),
    ('up', 'Upper sky and stars'),
    ('behind', 'Rear skyline'),
)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stage', choices=('preview4096', 'final'), default='final')
    args = parser.parse_args()
    stage = REVIEW / args.stage
    proof = json.loads((REVIEW / 'baseline.json').read_text(encoding='utf-8'))
    for record in proof['files']:
        assert sha(ROOT / record['preserved']) == record['sha256'], 'Preserved baseline changed'
    assert (stage / 'finish.json').is_file(), 'Finish the requested review stage first'
    rows = []
    for key, label in VIEWS:
        before = 'before/middle_ground_ingame_' + key + '.png'
        after = args.stage + '/consistency_ingame_' + key + '.png'
        assert (REVIEW / before).is_file() and (REVIEW / after).is_file(), 'Missing matched view: ' + key
        rows.append({'key': key, 'label': label, 'before': before, 'after': after})
    panorama = args.stage + '/consistency_sky_equirect.png'
    assert (REVIEW / panorama).is_file(), 'Missing whole-sky review'
    status = 'Candidate preview; not installed or native-build verified.' if args.stage != 'final' else 'Final art preview; native build verification pending.'
    build_link = ''
    state_preview = ''
    if (REVIEW/'blender_after_reveal.png').is_file():
        state_preview = '<figure><figcaption>After reveal · native card over the dull sky (approximate Blender display)</figcaption><a href="blender_after_reveal.png"><img src="blender_after_reveal.png" alt="After-reveal Blender preview"></a></figure>'
    if (REVIEW/'blender_before_jump.png').is_file():
        state_preview += '<details><summary>Before jump · Blender preview</summary><a href="blender_before_jump.png"><img loading="lazy" src="blender_before_jump.png" alt="Before-jump Blender preview"></a></details>'
    build_path = REVIEW / 'build.json'
    if args.stage == 'final' and build_path.is_file():
        build = json.loads(build_path.read_text(encoding='utf-8'))
        snapshot = pathlib.Path(build['snapshot'])
        saved = json.loads(snapshot.read_text(encoding='utf-8'))
        source = 'source_data/tod_skybox/_images/i_skybox_tod_cybercity.exr'
        assert sha(snapshot) == build['snapshot_sha256'], 'Build proof snapshot changed'
        assert sha(ROOT / source) == saved['inputs'][source]['sha256'], 'Installed sky no longer matches this proof'
        assert build['owned_sky_inputs_match_current'] and build['deployed_inputs_match_snapshot']
        status = 'Native sky build verified at ' + build['verified_at'] + '. User visual playtest pending.'
        if not build.get('current_source_parity'):
            status += ' The proof separately records later shared-source edits.'
        build_link = '<a href="build.json">Native build proof</a> · '
    options = ''.join('<option value="'+str(i)+'">'+html.escape(row['label'])+'</option>' for i, row in enumerate(rows))
    first = rows[0]
    document = '''<!doctype html><html lang="en"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Cybercity skyline consistency</title>
<style>
*{box-sizing:border-box}body{margin:0;background:#0b1018;color:#e4e9ee;font:16px/1.5 system-ui,sans-serif}
main{max-width:1500px;margin:auto;padding:30px}h1{font-size:30px;margin:0 0 10px}p{max-width:1050px}
a{color:#8dceee}select{padding:9px;background:#172233;color:inherit;border:1px solid #456075;border-radius:4px}
.pair{display:grid;grid-template-columns:1fr 1fr;gap:16px}figure{margin:16px 0}figcaption{padding:8px 0;color:#b2bdc9}
img{width:100%;height:auto;display:block;border:1px solid #293948}.status{border-left:3px solid #8dceee;padding:10px 16px;background:#141e2c}
.note{color:#b2bdc9;font-size:14px}details{margin:22px 0}summary{cursor:pointer}@media(max-width:850px){.pair{grid-template-columns:1fr}}
</style><main><h1>A shared cyber skyline, readable worlds</h1>
<p>The near buildings set the material and architecture family for the ordinary skyline. Compare the distant city, title supports and celestial detail at matched camera angles.</p>
<p class="status">STATUS</p>
<p class="note">These are projections of the finished Blender HDR sky at the established display bracket. They are not game screenshots; BO3 bloom and exposure remain a user playtest.</p>
<label for="view">Compare view </label><select id="view">OPTIONS</select>
<div class="pair"><figure><figcaption>Before · approved layout</figcaption><a id="beforeLink" href="BEFORE"><img id="before" src="BEFORE" alt="Previous sky"></a></figure>
<figure><figcaption>After · shipping sky alone, before-jump dull sign</figcaption><a id="afterLink" href="AFTER"><img id="after" src="AFTER" alt="Revised sky before the jump reveal"></a></figure></div>
<p class="note">The earlier sky had a permanently lit sign. The revised panorama intentionally contains the dull before-jump sign; after the crash a native card lights it. This title-state difference is separate from the city/material changes.</p>
STATE_PREVIEW
<details><summary>Whole panorama</summary><a href="PANORAMA"><img loading="lazy" src="PANORAMA" alt="Complete revised sky panorama"></a></details>
<p>BUILD<a href="composition_audit.json">Composition audit</a> · <a href="architecture_check.json">Geometry check</a> · <a href="baseline.json">Preserved baseline</a> · <a href="../../../tools/sky_consistency/README.md">Reproduction</a></p>
<p class="note">Reopen the installed Blender preview with tools/sky_consistency/open_preview.ps1 to restore Rendered mode and scene lighting after file loading.</p>
<p class="note">Gallery generated GENERATED.</p></main>
<script>const views=ROWS;document.querySelector('#view').addEventListener('change',e=>{const v=views[Number(e.target.value)];for(const side of ['before','after']){document.getElementById(side).src=v[side];document.getElementById(side+'Link').href=v[side];}});</script></html>'''
    replacements = {'STATUS': html.escape(status), 'OPTIONS': options, 'BEFORE': first['before'], 'AFTER': first['after'],
                    'PANORAMA': panorama, 'BUILD': build_link, 'GENERATED': datetime.datetime.now().astimezone().isoformat(),
                    'ROWS': json.dumps(rows), 'STATE_PREVIEW': state_preview}
    for key, value in replacements.items():
        document = document.replace(key, value)
    (REVIEW / 'review.html').write_text(document, encoding='utf-8')
    print('REVIEW_READY', REVIEW / 'review.html')


if __name__ == '__main__':
    main()
