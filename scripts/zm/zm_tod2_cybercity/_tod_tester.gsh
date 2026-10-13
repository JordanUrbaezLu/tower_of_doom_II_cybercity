// =============================================================================
// _tod_tester.gsh - THE CROWN TESTER KIT, one switch (2026-10-01).
//
// User 2026-10-01: "In the crown i want an option to switch between classes as
// well. I eventually want to push out a testing phase so testers have access to
// everything in the crown."
//
// TOD_TESTER_KIT 1 places the crown hall's CLASS TERMINAL (_tod_class_terminal.gsc):
// a data console against the west wall, opposite the crown crate, where any
// player can switch to any class for the rest of the run, keeping their tier
// and every upgrade card (a card of another class sleeps until they are that
// class again).
//
// It is ON in a release build ON PURPOSE when that release is the testing phase
// the user described. tools/build_map.ps1 -Publish therefore WARNS rather than
// refusing while it is 1: set it to 0 here for an ordinary release.
//
// Other crown test items keep their own switches for now (the partner test
// benches: TOD_PARTNER_TEST_BENCHES in _tod_partners.gsc, which -Publish still
// refuses). Folding them under this one switch is the obvious next step for the
// testing phase - one flag, one place to look.
// =============================================================================
// 2026-10-04: OFF for the first real playthrough (user: "prep for an actual play
// through"). With it on, the crown's class terminal is placed AND the Battle
// Arena's first trip opens at level 10 (TOD_ARENA_TEST_START_LEVEL in
// _tod_arena.gsc) - a real run must climb from level 1. Set it to 1 again for a
// testers' build.
#define TOD_TESTER_KIT 0
