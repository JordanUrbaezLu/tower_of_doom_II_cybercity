"""Assemble the rendered sweep frames and record review evidence."""
import hashlib, json, pathlib, subprocess
ROOT = pathlib.Path(__file__).resolve().parents[2]
ART = ROOT / 'art/crown_alarm'
OUT = ART / 'intensity_review'
frames = [OUT / 'frames' / (str(f).zfill(3) + '.png') for f in range(1, 37, 2)]
assert all(p.exists() for p in frames)
concat = OUT / 'frames.txt'
concat.write_text(''.join(f"file 'frames/{p.name}'\nduration 0.083333333\n" for p in frames), encoding='utf-8')
subprocess.run(['ffmpeg', '-y', '-hide_banner', '-loglevel', 'error', '-f', 'concat',
                '-safe', '1', '-i', str(concat), '-r', '12', '-t', '1.5',
                '-vf', 'scale=680:426', '-c:v', 'libx264', '-crf', '20',
                '-pix_fmt', 'yuv420p', '-movflags', '+faststart', str(OUT / 'sweep.mp4')], check=True)
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
profile = json.loads((ROOT / 'tools/crown_alarm/light_profile.json').read_text())
evidence = dict(profile=profile, status='RANDOM_PHASES_SOURCE_READY_UNBUILT',
    starting_angles=json.loads((OUT/'phases.json').read_text()),
    archived_playtest='tmp/elite_tracking/runs/20260926_153852_841_a5eddc36/console_mp.log',
    old_log='ON fixtures=30 local_spots=13 turn_seconds=1.5 reason=alarm_trigger',
    checks=['source mesh/image bindings', 'shipping initialization and alarm state transitions',
            'one server random draw per fixture; fixed housing and pendant pitch',
            'floor/cone geometry and culling bounds', '109-script arity', '7816 native-API sites'],
    review_limit='Blender relative light/motion study, not native BO3 calibration.',
    outputs={p.relative_to(ROOT).as_posix():sha(p) for p in
             [ART/'crown_alarm.blend', OUT/'before.blend', OUT/'stronger.blend',
              OUT/'before.png', OUT/'stronger.png', OUT/'sweep.mp4']},
    brightness_evidence='brightness_build8.json',
    built=False, game_launched=False, native_visual_verified=False)
(OUT / 'validation.json').write_text(json.dumps(evidence, indent=2) + '\n')
print('ALARM_REVIEW_READY: two matched images, 1.5s sweep, source evidence; native build pending')
