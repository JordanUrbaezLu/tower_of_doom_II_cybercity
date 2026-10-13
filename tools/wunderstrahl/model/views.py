"""The matched review views (before = untouched DG-2, after = Wunderstrahl). Gun space = native inches, X forward,
Y = the gun's left, Z up. The first-person view is posed by frame 0 of the REAL idle clip with the camera at tag_view
(origin, looking +X) at BO3's default 80 degree horizontal FOV - the necro-staff review recipe."""
import math
CENTRE = (14.8, 0.7, -0.6)
MUZZLE = (37.2, 0.0, 3.0)
VIEWS = {
    # name: (location, target, lens mm, ortho scale or None, resolution)
    'quarter_left': ((14.8 + 46, 0.7 + 60, -0.6 + 25), CENTRE, 50, None, (1600, 1000)),
    'quarter_right': ((14.8 + 46, 0.7 - 60, -0.6 + 25), CENTRE, 50, None, (1600, 1000)),
    'profile_left': ((14.8, 140.0, 1.0), (14.8, 0.0, 1.0), None, 60.0, (1800, 900)),
    'lens_close': ((53.5, 11.0, 9.0), MUZZLE, 70, None, (1600, 1000)),
    'lens_front': ((62.0, -3.5, 5.5), MUZZLE, 85, None, (1400, 1000)),
    'top': ((14.8, 0.7, 120.0), (14.8, 0.7, 0.0), None, 60.0, (1800, 900)),
}
WORLD_VIEW = ((14.8 + 70, 0.7 + 95, -0.6 + 40), CENTRE, 50, None, (1600, 1000))


def fp_camera_spec():
    return dict(location=(0.0, 0.0, 0.0), target=(100.0, 0.0, 0.0))
