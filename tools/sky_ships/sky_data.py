"""THE SKY FLEET shared data (docs/192): plain tables only, importable by Blender (sky_lib, the ship scripts) AND by
system Python (make_textures.py). One source for the colours, the marking atlas cells and the ad wall order."""

# Linear RGB. Neon accents are the tower's district colours; engines run hot (near white); running lights saturated.
GLOW = {
    'red':       (1.00, 0.07, 0.05),
    'cyan':      (0.08, 0.82, 1.00),
    'magenta':   (1.00, 0.10, 0.72),
    'green':     (0.14, 1.00, 0.30),
    'orange':    (1.00, 0.40, 0.05),
    'amber':     (1.00, 0.62, 0.12),
    'gold':      (1.00, 0.74, 0.18),
    'white':     (1.00, 0.97, 0.92),
    'hot_cyan':  (0.62, 0.93, 1.00),   # engine core
    'hot_amber': (1.00, 0.70, 0.36),   # engine core, warm drives
    'nav_red':   (1.00, 0.04, 0.03),
    'nav_green': (0.10, 1.00, 0.18),
    'teal':      (0.05, 0.95, 0.80),
}
# The hauler's cargo: saturated so it reads at night even lit only by the moon.
CARGO = {'cargo_orange': (0.95, 0.36, 0.06), 'cargo_teal': (0.05, 0.62, 0.62), 'cargo_red': (0.80, 0.06, 0.05),
         'cargo_white': (0.82, 0.84, 0.86), 'cargo_yellow': (0.95, 0.70, 0.08)}
# Marking atlas i_tod_sky_deco_c (1024 x 512) cells, pixel boxes (x0, y0, x1, y1).
DECO_CELLS = {'tod01': (0, 0, 640, 170), 'haul07': (0, 170, 640, 300), 'gs13': (0, 300, 640, 420),
              'crown': (704, 22, 960, 278), 'chevrons': (660, 300, 1020, 360), 'arrows': (660, 390, 1016, 450)}
# The ad wall i_tod_sky_ads_c (2048 x 1024, 4 x 2 cells of 512): the sky's own neon ads (art/sky3d/billboards).
AD_ORDER = ['ad_01', 'ad_02', 'ad_04', 'ad_05', 'ad_07', 'ad_08', 'ad_09', 'ad_11']   # OBEY DOOM SLEEP RISE VOID BUY DRINK ASCEND
AD_ORDER_B = ['ad_04', 'ad_08', 'ad_02', 'ad_05', 'ad_09', 'ad_01', 'ad_07', 'ad_12']   # SLEEP BUY DOOM RISE DRINK OBEY VOID bottle
