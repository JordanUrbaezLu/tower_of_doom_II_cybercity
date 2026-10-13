# screenshot_fit — where is the sky's sign IN GAME? (docs/196 §3)

Two readings of the sky's in-game orientation were written down, gated, built and wrong
(`yaw = 90 - roll`, then `yaw = -roll + skyRotation`). The third was MEASURED from one user
screenshot and it holds: **the image's centre column faces world yaw -(SSI sun azimuth +
skyRotation) - roll** (`tools/test_jumppad.js` applies it). If the sky ever moves again,
measure, never predict.

## What you need

- A screenshot where part of the sign is visible, with some level geometry in view (the
  heading comes from the geometry: the sky is at infinity).
- The eye it was taken from: the console log's `[TOD_AI] PLAYER ... pos=(x, y, z)` at that
  moment (match the HUD's HP or points), + 60 standing.

## Run it

```
node   tools/sky3d/screenshot_fit/export_brushes.js --eye -6.4,632.4,19452.1
python tools/sky3d/screenshot_fit/fit.py tools/sky3d/screenshot_fit/case_20260929.json
```

Write a new `case_*.json` per screenshot: the shot, the eye, the HUD rectangles to ignore, the
search ranges, and 4+ painted features matched between
`art/sky3d/sign/tod2_title_gate_reference.png` (px) and the screenshot (px). It prints the view
(yaw / pitch / hfov), the sign's WORLD yaw, and writes `tmp/screenshot_fit/compare.png` (the
screenshot above the rebuilt view). **The rebuilt view must reproduce the screenshot** before
you trust the number.

## The 2026-09-29 result (`case_20260929.json`)

View yaw 83 (from the geometry), pitch -1.6 and hfov 101.9 (from the sign fit, 10 px rms over
six features). The sign's centre is 41.6 deg right of the view, at **world yaw 41.4 +- 1.5**,
with skyRotation 180 / roll 0 / sun 140. The rule predicts 40. The fix was skyRotation 40 (the
sign due west). ~40 s on this PC.

The mask grid only fixes the HEADING; its pitch / hfov land on the grid's edges and are not used.
The check image is drawn with the sign fit's pitch and hfov.

`view.py` is also a quick first-person silhouette renderer of the generated map (ray-cast
convex brushes, tile-culled, ~0.5 s per frame at 474 x 259).
