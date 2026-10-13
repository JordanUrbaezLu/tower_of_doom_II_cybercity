"""Review helper: the sign at fault frame 151 (C sparks, C/E/T dark)."""
import bpy
from pathlib import Path
bpy.context.scene['shop_review_view']='fault';bpy.context.scene['shop_review_frame']=152
exec(compile(Path(__file__).with_name('19_review_view.py').read_text(),str(Path(__file__).with_name('19_review_view.py')),'exec'))
bpy.context.scene['shop_review_frame']=1
