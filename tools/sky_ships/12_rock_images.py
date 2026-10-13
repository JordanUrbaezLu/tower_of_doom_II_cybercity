"""Point the asteroids' rock images at the committed textures (model_export/tod_sky_ships/_images) instead of the
first preview's staging copies; the bytes are the same (make_textures.py generates both)."""
import bpy, sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import sky_lib
done = []
for im in bpy.data.images:
    if im.name.startswith('i_tod_sky_rock'):
        p = sky_lib.TEX / (im.name + '.png')
        assert p.exists(), p
        im.filepath = str(p)
        im.reload()
        done.append(im.name)
print('SKY_ROCK_IMAGES', sorted(done))
