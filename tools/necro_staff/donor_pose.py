from pathlib import Path
source=Path(__file__).with_name('motion_preview.py').read_text()
source=source.replace("cases=[('idle',", "cases=[('idle',")
a=source.index('cases=');b=source.index('\nhandpath=',a)
source=source[:a]+"cases=[('ice_donor', 'tod_vm_necro_staff_fit_idle',0)]"+source[b:]
source=source.replace("for tier in [2,3]:", "for tier in [3]:")
source=source.replace("ROOT/f'model_export/tod_necro_staff/tod_necro_staff{tier}_view_lod0.XMODEL_BIN'", "native_path('model_export',asset('xmodel','tod_bo6_ice_vm')['filename'])")
source=source.replace("handmat if hands else bpy.data.materials[material.name]", "handmat")
source=source.replace("ART/'first_person_review.blend'", "ART/'donor_pose_review.blend'")
exec(compile(source,__file__,'exec'))
