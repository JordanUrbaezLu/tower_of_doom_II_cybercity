"""
tools/sky3d/segment_title_gate.py — the title gate's MODEL masks (docs/166 §9). Run once per new reference image.

The sky's title sign is the user's reference painting (art/sky3d/sign/tod2_title_gate_reference.png) cut out of its
background. The cut starts from two masks of BiRefNet-DIS5K (dichotomous image segmentation: trained on objects with
fine structure — gates, fences, towers), which is the only model tried that finds the WHOLE gate:
  * the general BiRefNet found only the text panel (it reads as a logo); BiRefNet-COD found only the skull;
  * DIS5K at 1024 finds the gate with its pillars and lattice columns, soft edges;
  * DIS5K at 2048 draws the upper silhouette crisply (orb rings, crest spikes, railing bars) but drops the pillar bodies.
tools/sky3d/cut_title_gate.py combines the two and applies the hand edits. Both masks are committed next to the
reference, so the cut never needs this script or its dependencies.

RUN (a Python with torch, torchvision, transformers, timm, einops, kornia — kept OUT of the system Python, e.g. a venv
created with --system-site-packages; weights ~450 MB each, cached under HF_HOME):
  python tools/sky3d/segment_title_gate.py [--ref art/sky3d/sign/tod2_title_gate_reference.png]
Writes art/sky3d/sign/tod2_title_gate_dis5k_1024.png and _2048.png (8-bit, the reference's size).
Measured 2026-09-29 on the laptop's CPU: 34 s (1024), 70 s (2048).
"""
import os, sys, time
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, '..', '..'))
SIGN = os.path.join(REPO, 'art', 'sky3d', 'sign')
REF = sys.argv[sys.argv.index('--ref') + 1] if '--ref' in sys.argv else os.path.join(SIGN, 'tod2_title_gate_reference.png')

import torch
from transformers import AutoModelForImageSegmentation

torch.set_num_threads(os.cpu_count())
model = AutoModelForImageSegmentation.from_pretrained('ZhengPeng7/BiRefNet-DIS5K', trust_remote_code=True).float().eval()   # the weights ship fp16
im = Image.open(REF).convert('RGB')
for size, tag in (((1024, 1024), '1024'), ((2048, 1536), '2048')):
    t = time.time()
    x = np.asarray(im.resize(size, Image.BICUBIC)).astype(np.float32) / 255.0
    x = (x - np.array([0.485, 0.456, 0.406], np.float32)) / np.array([0.229, 0.224, 0.225], np.float32)
    with torch.no_grad():
        p = model(torch.from_numpy(x.transpose(2, 0, 1)[None].copy()))[-1].sigmoid()[0, 0].numpy()
    out = os.path.join(SIGN, f'tod2_title_gate_dis5k_{tag}.png')
    Image.fromarray((np.clip(p, 0, 1) * 255).astype(np.uint8)).resize(im.size, Image.BICUBIC).save(out)
    print(f'[segment] {tag}: {time.time() - t:.1f} s -> {out}')
