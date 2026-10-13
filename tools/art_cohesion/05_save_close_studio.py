"""Save and close only the dedicated shared-material MCP studio."""
import bpy,pathlib,json,hashlib,datetime
ROOT=pathlib.Path(__file__).resolve().parents[2];ART=ROOT/'art/cybercity_materials'
path=pathlib.Path(bpy.data.filepath).resolve();assert path.parent==ART and path.name in ('native_comparison.blend','crown_complete.blend'),path
bpy.ops.wm.save_as_mainfile(filepath=str(path))
record={'saved':datetime.datetime.now().isoformat(),'file':path.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'objects':len(bpy.data.objects),'original_prop_masters_changed':False}
(ART/(path.stem+'_saved.json')).write_text(json.dumps(record,indent=2))
def close():bpy.ops.wm.quit_blender()
bpy.app.timers.register(close,first_interval=2)
print('SHARED_STUDIO_SAVED_AND_CLOSING',record,flush=True)
