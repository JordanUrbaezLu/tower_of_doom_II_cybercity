# Teleporter status art

User correction, September 26: OFF has no device lights; READY is green; PENDING is an animated yellow chase. No pink. The accepted metal finish stays intact.

Master: teleporter_cyber.blend, MCP port 9879. Original 446 parts and baked body retained. Eighteen yellow arc segments form a quarter-circle chase rotating once every three seconds, with three brightness bands. Manual scene teleporter_state: 0 off, 1 ready, 2 pending; teleporter_preview_auto=0 enables manual control.

Native: same seven body LODs, green and zero-emission material twins, one 1,152-triangle yellow indicator while powered but pending (destination lock, cooldown or upgrade pause). Explicit shutdown and no power are dark. Ready FX is green; charge overlay yellow; release overlay green. Stock teleport bursts retain their original electricity. Triggers, 0.8-second travel charge and 60-second cooldown are preserved. No additional particles or dynamic lights.

Blender proves authored shape/timing; BO3 appearance and runtime output require the user playtest. Read docs/162_lighting/03_glow_and_perks.md; untested shader/light claims remain untested.
