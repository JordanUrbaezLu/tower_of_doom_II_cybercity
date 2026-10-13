"""Read-only image-path audit of fleet authoring/review .blend files in fresh background Blender.

Run with blender --background --python tools/sky_ships/17_audit_image_paths.py.
Append only image datablocks, without saving either file or touching the user's
visible studio. A current blend cannot append itself, so use a fresh background
process. Writes an audit receipt under tmp only.
"""
import bpy,json,pathlib
ROOT=pathlib.Path(__file__).resolve().parents[2]
records=[]
for rel in ('art/sky_ships/sky_fleet.blend','art/sky_ships/sky_fleet_realism_preview.blend'):
    path=ROOT/rel
    existing=set(bpy.data.images)
    with bpy.data.libraries.load(str(path),link=False) as (src,dst):
        dst.images=list(src.images)
    images=[]
    for im in dst.images:
        if im is None:continue
        packed=bool(im.packed_file) or bool(im.packed_files)
        raw=im.filepath
        resolved=pathlib.Path(bpy.path.abspath(raw,library=im.library)).resolve() if raw else None
        relative=resolved.relative_to(ROOT).as_posix() if resolved and resolved.is_relative_to(ROOT) else None
        temporary=bool(relative and (relative.startswith('tmp/') or '/tmp/' in relative))
        durable=packed or bool(relative and not temporary and resolved.exists())
        images.append(dict(name=im.name,raw_path=raw,resolved=str(resolved) if resolved else None,
                           repo_path=relative,packed=packed,temporary=temporary,durable=durable,
                           source=im.source))
    for im in dst.images:
        if im is not None and im not in existing and im.users==0:
            bpy.data.images.remove(im)
    records.append(dict(blend=rel,images=images,bad=[im for im in images if im['source']=='FILE' and not im['durable']]))
out=ROOT/'tmp/sky_realism/image_path_audit.json'
out.write_text(json.dumps(records,indent=2))
print('FLEET_IMAGE_PATH_AUDIT',json.dumps([dict(blend=r['blend'],images=len(r['images']),bad=r['bad']) for r in records]))
assert not any(r['bad'] for r in records),'Non-durable fleet image reference; inspect '+str(out)
