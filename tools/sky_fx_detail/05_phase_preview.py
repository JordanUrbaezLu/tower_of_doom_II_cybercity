"""MCP: compact animation of the authored detail layers, without native extras."""
import bpy,pathlib
ROOT=pathlib.Path(__file__).resolve().parents[2]
OUT=ROOT/'tmp/sky_fx_detail/staged'
scene=bpy.context.scene
scene.render.resolution_x=640;scene.render.resolution_y=426
scene.cycles.samples=6
for frame in (1,7,13,19,25,31,37,43,49):
    scene.frame_set(frame)
    scene.render.filepath=str(OUT/('layer_phase_%02d.png'%frame))
    bpy.ops.render.render(write_still=True)
scene.frame_set(25)
print('SKY DETAIL PHASE PREVIEW READY')
