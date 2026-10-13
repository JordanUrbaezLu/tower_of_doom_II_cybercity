"""Review helper: frame the 'counter' view (see 19_review_view.py)."""
import bpy
from pathlib import Path
bpy.context.scene['shop_review_view']='counter'
exec(compile(Path(__file__).with_name('19_review_view.py').read_text(),str(Path(__file__).with_name('19_review_view.py')),'exec'))
