"""Deterministic physical surface detail for the fleet; all channels share wear masks.

Subtle coating chips collect at panel lips, oxidation stays in joints, wiped scuffs
interrupt paint gloss; rocks have mineral inclusions and broken fine fractures.
These are exported native textures, not a preview-only procedural shader.
"""
import numpy as np
from functools import lru_cache
from PIL import Image, ImageDraw


def scuffs(n, seed, count):
    """Sparse, directional handling scratches with broken ends; periodic at the tile seam."""
    rng = np.random.default_rng(seed)
    image = Image.new('L', (n, n), 0)
    d = ImageDraw.Draw(image)
    for _ in range(count):
        x, y = rng.uniform(0, n, 2)
        length = rng.uniform(3, 32) * n / 1024
        angle = rng.normal(-0.12, 0.2)
        end = (x + np.cos(angle) * length, y + np.sin(angle) * length)
        value = int(rng.integers(65, 215))
        for ox in (-n, 0, n):
            for oy in (-n, 0, n):
                d.line((x+ox, y+oy, end[0]+ox, end[1]+oy), fill=value, width=max(1, n//1024))
    return np.asarray(image, dtype=np.float64) / 255


def plating(c, h, g, s, seed, noise):
    n = h.shape[0]
    fine = noise(n, n/4, seed+301)
    medium = noise(n, 64, seed+302)
    broad = noise(n, 13, seed+303)
    low = np.minimum.reduce([np.roll(h, k, a) for a in (0, 1) for k in (-3, 3)])
    edge = np.clip((h-low)*5, 0, 1)
    cavity = np.clip((0.32-h)*4, 0, 1)
    chip = edge * np.clip((medium + fine*0.5 - 0.04)*3.8, 0, 1)
    oxidation = cavity * np.clip((broad+0.25)*1.25, 0, 0.75)
    scratch = scuffs(n, seed+304, 520) * np.clip(0.65+medium, 0, 1)
    # Slight warm contamination in recesses; clean exposed alloy on raised lips.
    c = c * (1 + 0.09*broad + 0.025*fine)[..., None]
    c = c*(1-oxidation[..., None]*0.65) + np.array((0.11, 0.053, 0.022))*oxidation[..., None]*0.3
    exposed = np.maximum(chip*0.78, scratch*0.32)
    c = c*(1-exposed[..., None]) + np.array((0.28, 0.285, 0.295))*exposed[..., None]
    h = h + 0.025*fine - 0.055*chip - 0.036*scratch
    g = g + 0.075*medium + 0.12*chip + 0.06*scratch - 0.16*oxidation
    s = s + 0.12*chip + 0.05*scratch - 0.075*oxidation
    return np.clip(c, 0, 1), h, np.clip(g, .12, .84), np.clip(s, .04, .55)


@lru_cache(maxsize=1)
def cargo_layers(n, noise):
    """The five coatings share one wear layout, computed only once per generation."""
    broad = noise(n, 7, 5011)
    medium = noise(n, 65, 5012)
    grain = noise(n, n/3, 5013)
    run = noise(n, 20, 5014)
    scratch = scuffs(n, 5015, 370)
    # Handling abrasion is scarce: intact painted surface remains the majority.
    chip = np.clip((medium + .45*grain - .39)*4.5, 0, 1)
    grime = np.clip((broad + .35)*.42, 0, .44)
    oxide = np.clip((run+.2)*.6, 0, .5)*chip
    paint = 1-.23*grime+.11*medium+.022*grain
    worn = np.maximum(chip*.83, scratch*.4)
    metal = np.array((.18, .17, .155))[None, None, :]*(1-oxide[..., None])
    h = .025*grain - .13*chip - .05*scratch
    g = np.clip(.40+.09*medium+.14*chip+.1*scratch-.18*grime, .16, .75)
    s = np.clip(.052+.13*chip+.04*scratch-.025*grime, .02, .25)
    return paint, worn, metal, h, g, s


def cargo(n, rgb, noise):
    """Weathered enamel, distinct from plated alloy; retains the existing color identity."""
    paint, worn, metal, h, g, s = cargo_layers(n, noise)
    c = np.array(rgb)[None, None, :]*paint[..., None]
    c = c*(1-worn[..., None])+metal*worn[..., None]
    return np.clip(c, 0, 1), h, g, s


def fractures(n, noise):
    """Warped, interrupted Voronoi fracture network; no painted directional lighting."""
    rng = np.random.default_rng(7791)
    yy, xx = np.mgrid[0:n, 0:n].astype(np.float64)
    xx += 18*noise(n, 26, 7792)
    yy += 18*noise(n, 29, 7793)
    nearest, second = np.full((n, n), 1e12), np.full((n, n), 1e12)
    for cx, cy in rng.uniform(0, n, (30, 2)):
        dx, dy = (xx-cx+n/2)%n-n/2, (yy-cy+n/2)%n-n/2
        dist = np.sqrt(dx*dx+dy*dy)
        second = np.minimum(second, np.maximum(nearest, dist))
        nearest = np.minimum(nearest, dist)
    delta = second-nearest
    broken = np.clip((noise(n, 22, 7794)+.19)*2.8, 0, 1)
    cracks = np.exp(-(delta/1.45)**2)*broken
    shoulders = np.exp(-((delta-3.4)/2.5)**2)*broken
    mineral = np.clip((noise(n, 82, 7795)+.28*noise(n, 320, 7796)-.26)*3, 0, 1)
    return cracks, shoulders, mineral


def drive_metal(n, noise):
    """Bare nozzle alloy: heat-temper film, shallow lathe grain, sparse soot and scuffs.

    Assigned only to engine-bell meshes; painted armor keeps its separate finish.
    No glow or baked directional highlight is present in these maps.
    """
    yy, xx = np.mgrid[0:n, 0:n]
    broad = noise(n, 9, 9101)
    medium = noise(n, 48, 9102)
    grain = noise(n, n/3, 9103)
    film = .5+.5*np.sin(2*np.pi*(yy/n*4+.32*broad))
    soot = np.clip((broad+.28)*.48, 0, .38)
    scratch = scuffs(n, 9104, 220)
    bronze, blue = np.array((.17,.12,.072)), np.array((.073,.108,.17))
    tint = bronze[None,None,:]*(1-film[...,None])+blue[None,None,:]*film[...,None]
    c = np.array((.17,.18,.195))[None,None,:]*.70+tint*.30
    c = c*(1-soot[...,None])*(1+.10*medium[...,None]+.025*grain[...,None])
    c = c*(1-.2*scratch[...,None])+np.array((.24,.255,.275))*.2*scratch[...,None]
    h = .022*grain+.006*np.sin(yy*2*np.pi/5)-.035*scratch
    g = np.clip(.58+.075*medium-.28*soot+.10*scratch,.25,.82)
    s = np.clip(.16+.05*medium-.09*soot+.09*scratch,.05,.3)
    return np.clip(c,0,1), h, g, s


def mineral(n, noise):
    """Natural luminous mineral: intact bright crystal with sparse dark inclusions.

    The peak is unchanged; only micro-fractures and inclusions interrupt emission.
    Dedicated rock materials keep this breakup off the manufactured ship lights.
    """
    broad=noise(n,12,9301);medium=noise(n,65,9302);grain=noise(n,n/3,9303)
    cracks=np.exp(-(np.abs(noise(n,24,9304)+.2*medium)/.013)**2)
    cracks*=np.clip((broad+.45)*1.3,0,1)
    inclusion=np.clip((medium+.35*grain-.27)*6,0,1)
    mask=np.clip((.94+.065*broad+.025*grain)*(1-.78*cracks)*(1-.985*inclusion),.008,1)
    h=.022*grain-.10*cracks-.055*inclusion
    g=np.clip(.55+.12*medium+.06*grain-.28*inclusion,.18,.8)
    s=np.clip(.08+.025*medium-.04*inclusion,.025,.14)
    return mask,h,g,s
