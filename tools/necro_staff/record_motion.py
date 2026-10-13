"""Record a completed MCP motion render; never treat stale frames as current."""
import pathlib,json,hashlib,datetime
ROOT=pathlib.Path(__file__).resolve().parents[2];ART=ROOT/'art/necro_staff'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
start=max((ART/name).stat().st_mtime for name in ['animations.json','models.json'])
frames=sorted((ART/'motion').glob('*.png'))
assert len(frames)==32 and all(p.stat().st_mtime>start for p in frames),'Incomplete or stale casting preview'
blend=ART/'casting_motion_review.blend';assert blend.stat().st_mtime>=max(p.stat().st_mtime for p in frames)
data=dict(frames=[dict(file=p.relative_to(ROOT).as_posix(),sha256=sha(p)) for p in frames],blend=blend.relative_to(ROOT).as_posix(),blend_sha256=sha(blend),animations_sha256=sha(ART/'animations.json'),models_sha256=sha(ART/'models.json'),recorded_at=datetime.datetime.now().isoformat(),native_visual_verified=False,note='Actual Blender MCP render completed all 32 samples and saved the final scene after the transport timeout. Fresh frame and saved-scene timestamps are checked against current model/animation metadata. Neutral review lighting only; no in-game visual verification.')
(ART/'motion.json').write_text(json.dumps(data,indent=2))
print('MOTION RECEIPT: 32 fresh frames and final Blender scene match current model/animation metadata')
