# Electrical detail and mask breathing — September 24

User follow-up: add design on the left, all sign letters must work, exactly
three blink, occasional sparks, animate the left canister, and slowly pulse
the eyes/mouth. This supersedes permanently unlit E/O.

Live Blender MCP art/animation and authored native controller. Six-second loop, 30 fps, frames 1–180;
frame 181 equals frame 1. Black/oxblood/red palette retained. Assess from the
player-facing front and left oblique view, plus a canister detail view.

| Layer | Shape / scale | Timing |
|---|---|---|
| Sign | Existing bent red neon; all eight letters functional | T/H retain earlier stutters; E adds short dips at 1.8 and 3.8 s; I/M/S/O/P steady |
| Sign discharge | Tiny branched arcs at faulty terminals plus short amber/red flecks; no whole-window flash | 2–4 frame arcs, 6–12 frame flecks on selected flicker events |
| Left service bay | Layered black panels, copper pressure piping, an insulated caged red core, connectors and fins | Core breathes over 3 s; four small segments chase vertically |
| Left counter component | Existing red-lit actuator merchandise | Quiet pulse and a brief small contact arc |
| Existing tall side core | Existing caged red core, preserved | Matching slow pulse and occasional local contact spark |
| Merchant mask | Existing red X eyes and uneven grin; body stays still, hands below counter | Smooth 6 s dim/bright/dim cycle, eyes/mouth together; existing damaged wires remain weaker |
| Pressure assembly | Red three-spoke handwheel and physical gauge needle | 3 s wheel turn/return, 0–20.6 degrees; smaller gauge motion with fast chatter |
| Sound | Three short cuts from the supplied electricity WAV; positional and restrained | Native sound and spark start from the same event callback; 170/230/310 ms, no randomized pitch/delay |
| Powered off | Physical hut and inventory retained, vendor absent | Emission, FX and audio off; valve and gauge rest; no sky marker |

The largest lights are the lettering and face. Sparks remain local to equipment,
are short and sparse, and never cover the merchant or fill the service window.
No extra flashing dynamic lights. Mesh/curve sparks are separate preview FX.
Representative authored arc and fleck geometry is explicitly exported as native
models, then driven by two native one-shot emitters. Six particles/event,
maximum twelve overlapping, lifetime at most 310 ms, bounds +/-18 units.
They are independent of the hut/vendor. Blender animation alone is not the
native implementation. The stock Wunderfizz sky marker is additional cost.

Native integration uses BO3-owned models/materials/emitters with explicit
start/stop/host cleanup, the vendor's active-shop-only lifetime, and automatic
transition logs. Three crown copies share one active timeline. Build evidence
is under tmp/partner_shop_build. Native appearance, overdraw, lifecycle and
measured cost await the user's playtest per docs/155; no game launch.
