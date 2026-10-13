// =============================================================================
// _tod_eye_glow.gsh - THE HORDE'S EYES, the names (PK04, 2026-10-04).
//
// The stock eye-glow particles every zombie wears were ORANGE (zm_usermap.csc:72,
// "zombie/fx_glow_eye_orange") over the charcoal horde's pure-red eyes and the
// golden zombie's gold ones. _tod_eye_glow.csc points the stock eye lane at the
// two effects below instead (tools/fxgen/horde_eyes/make_fx.py GENERATES them).
//
// WHO READS THIS FILE - keep this list true, it is the whole contract:
//   scripts/zm/zm_tod2_cybercity/_tod_eye_glow.csc     precache + the override
//   scripts/zm/zm_tod2_cybercity/_tod_cyber_zombies.gsc  its dev START line names them
//   tools/fxgen/horde_eyes/test_eye_glow.js            LOCKSTEP: the generator's
//       effect paths, the zone's fx lines and _tod_golden_zombie.gsc's
//       TOD_GOLDEN_MODEL_BODY must match these three strings.
// =============================================================================

#define TOD_EYE_FX_HORDE       "tod/cyber/fx_tod_charcoal_eye_glow_red"   // every ordinary zombie (charcoal horde, armored sprinters)
#define TOD_EYE_FX_GOLDEN      "tod/cyber/fx_tod_golden_eye_glow"         // the golden zombie (docs/197)
#define TOD_EYE_GOLDEN_BODY    "tod_golden_zombie_body"                   // LOCKSTEP _tod_golden_zombie.gsc TOD_GOLDEN_MODEL_BODY
