"""Bake only the two new crown tiles; retain the original twenty maps."""
import pathlib
ROOT=pathlib.Path(__file__).resolve().parents[2]
code=(ROOT/'tools/art_cohesion/02_bake_kit.py').read_text()
code=code.replace("cybercity_material_library.blend","crown_surface_library.blend").replace("('floor','wall','ceiling','trim')","('armor','crystal')")
code=code.replace("scene.render.filepath=str(ART/'authored_tiles.png');bpy.ops.render.render(write_still=True)","# Original four-tile render retained")
code=code.replace("ART/'bake_manifest.json'","ART/'crown_bake_manifest.json'")
exec(compile(code,str(ROOT/'tools/art_cohesion/02_bake_kit.py'),'exec'))
