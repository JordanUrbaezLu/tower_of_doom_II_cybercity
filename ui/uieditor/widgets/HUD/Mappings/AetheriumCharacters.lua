require( "ui.uieditor.widgets.HUD.AetheriumWidgets.TodHealthTint" )

-- Aetherium Character Portrait Mappings
-- Maps BO3 character IDs to custom portrait icons

CoD.AetheriumCharacters = {
	-- Primis Crew (Origins/Der Eisendrache/etc.)
	["uie_t7_zm_hud_score_char1"] = "i_mtl_ui_icon_operators_nikolai",     -- Nikolai
	["uie_t7_zm_hud_score_char2"] = "i_mtl_ui_icon_operators_takeo",       -- Takeo
	["uie_t7_zm_hud_score_char3"] = "i_mtl_ui_icon_operators_dempsey",     -- Dempsey
	["uie_t7_zm_hud_score_char4"] = "i_mtl_ui_icon_operators_richtofen",   -- Richtofen

	-- =====================================================================
	-- SHADOWS OF EVIL BODIES -> CLASS ICONS (v16.19, 2026-09-02)
	--
	-- _tod_classes.gsc binds a player's body to their CLASS (bodytype 5/6/7/8
	-- = boxer/detective/femme/magician -> heavy/assault/skirmisher/slasher),
	-- so the model IS the class and a class icon is the *consistent* portrait,
	-- not a substitution. It is also the more useful read in co-op: on a
	-- 50-floor spiral you want to know a teammate's ROLE, not their face.
	--
	-- WHY THESE FOUR IDs: core_common.csv ships exactly EIGHT portrait images
	-- (char1..char8) for NINE player bodies. char1-4 are the Primis four above.
	-- The remaining SoE playables are boxer/detective/femme/magician, and the
	-- ninth body (index 4, the SoE Beast) is a transform state rather than a
	-- crew member, so it is almost certainly the one with no portrait — which
	-- lands char5..char8 on our four in index order.
	--
	-- ^ THAT ORDERING IS REASONED, NOT OBSERVED, and it cannot be derived by
	-- arithmetic: the Primis block above maps char1..char4 to indices 1,3,0,2,
	-- so charN is NOT index N-1. If a playtest shows two classes wearing each
	-- other's icon, permute these four lines — nothing else needs to change.
	--
	-- v16.57 (2026-09-02) — OBSERVED: a HEAVY (body index 5) saw the SLASHER
	-- medallion, i.e. index 5 reports char8. Both natural orderings explain it
	-- the same way — either the bodies index alphabetically (boxer 5 .. magician
	-- 8) and the portraits follow the SoE crew order (Nero, Jessica, Jack,
	-- Floyd = char5..8), or the reverse — and under EITHER the index->char map
	-- is a REVERSAL (5->8, 6->7, 7->6, 8->5). So the four lines below are the
	-- v16.19 order reversed, which yields the right icon for every class under
	-- both readings. If any class still wears another's icon, report WHICH saw
	-- WHICH and permute again.
	-- =====================================================================
	-- MEDALLIONS, not the bare i_tod_class_* glyphs (v16.20, 2026-09-02): the
	-- portrait slot is 35x40 (AetheriumPartyPlayers.lua:191-195) and the bare
	-- glyphs are 224x196 landscape line art — squashed to a different aspect and
	-- scaled ~6x down, their thin strokes disappear. The 256x256 medallions are
	-- square, and their glowing ring gives a hard outer edge that survives the
	-- downscale, which is what makes them legible at portrait size.
	-- v16.71 (2026-09-03) — SECOND OBSERVATION: a SLASHER (magician, body 8)
	-- saw the ASSAULT medallion, i.e. body 8 reports char7. With v16.57
	-- (boxer 5 -> char8) that kills BOTH natural orderings: the char id is
	-- baked per character asset, not derived from the index, and can only be
	-- OBSERVED. Observed so far: 5 -> char8 (heavy), 8 -> char7 (slasher).
	-- char5/char6 are the detective/femme pair in an order nobody has seen
	-- yet; assault on 5 is the working guess — if an ASSAULT sees the
	-- skirmisher medallion (or vice versa), swap those two lines only.
	-- v16.73 (2026-09-03) — THIRD OBSERVATION closes the table: an ASSAULT
	-- (detective, body 6) saw the skirmisher medallion, i.e. body 6 reports
	-- char6, so char5 is the femme by elimination. All four are observed now:
	-- boxer 5 -> char8, detective 6 -> char6, femme 7 -> char5, magician 8 -> char7.
	-- char5 (femme, body 7) is the NECROMANCER's body since 2026-09-26; its
	-- medallion landed the same day (docs/179).
	["uie_t7_zm_hud_score_char5"] = "i_tod_class_medallion_necromancer",   -- femme (7) -> char5, by elimination (above)
	["uie_t7_zm_hud_score_char6"] = "i_tod_class_medallion_assault",       -- OBSERVED 2026-09-03: detective (6) -> char6
	["uie_t7_zm_hud_score_char7"] = "i_tod_class_medallion_slasher",       -- OBSERVED 2026-09-03: magician (8) -> char7
	["uie_t7_zm_hud_score_char8"] = "i_tod_class_medallion_heavy",         -- OBSERVED 2026-09-02: boxer (5) -> char8

	-- Fallback. NOT "blacktransparent" any more: an unmapped id used to render
	-- an invisible portrait, which reads as a broken HUD rather than as a
	-- missing mapping. An operator face is never blank, makes no claim about
	-- the player's class, and is visually unmistakable against the four class
	-- icons — so if one ever shows up in the party list, the id above is wrong.
	["default"] = "i_mtl_ui_icon_operators_dempsey"
}

-- ===========================================================================
-- CLASS-ONLY PORTRAIT (v17.3, 2026-09-03 — user: "Before you select a class
-- there is a placeholder image. Can we remove that? Its dempsey and then
-- switches after I select, so it should be there [only then]").
--
-- THE PORTRAIT SLOT IS A CLASS BADGE, and before the draft resolves nobody has
-- a class. Until now that window drew an operator face, because a player spawns
-- on a stock Primis body whose char id maps to one of the four `operators_*`
-- entries above — so it was a VALID mapping firing in a state the table was
-- never asked about, not the `default` fallback misbehaving. Either way the
-- player saw Dempsey for the length of the draft and then a medallion.
--
-- This returns the icon ONLY when it resolves to a class medallion, and nil
-- otherwise. Both call sites draw `blacktransparent` on nil, which keeps them
-- clear of the party widget's own slot-occupancy alpha logic — setting alpha
-- here would be immediately overwritten by the playerScoreShown handler.
--
-- WHAT THIS COSTS: the operator faces stop being the "this mapping is broken"
-- canary the fallback comment above describes. Acceptable now and not before —
-- all four char ids were OBSERVED and closed on 2026-09-03 (v16.73), so the
-- table is complete. If a mapping ever does break, the symptom becomes an
-- ABSENT portrait rather than a wrong face; that is still visible, and it no
-- longer costs every player a wrong face during every draft.
-- ===========================================================================
function CoD.GetClassPortrait(characterID)
	local icon = CoD.GetCharacterPortrait(characterID)
	if icon and string.sub(icon, 1, 22) == "i_tod_class_medallion_" then
		return icon
	end
	return nil
end

-- Helper function to get character portrait icon
function CoD.GetCharacterPortrait(characterID)
	if not characterID or characterID == "" then
		return CoD.AetheriumCharacters["default"]
	end
	
	-- Check if mapping exists
	if CoD.AetheriumCharacters[characterID] then
		return CoD.AetheriumCharacters[characterID]
	end
	
	-- Fallback to default
	return CoD.AetheriumCharacters["default"]
end

-- [tod v18.39] THE HP TEXT + TINT REPAINT (the name is historical; every
-- class's health plate calls it).
--
-- Lives HERE, not in AetheriumPlayerInfo.lua, because that widget is at its
-- compiled ceiling: it accepts a changed VALUE on an existing line but not one
-- added statement, in either of its closures (proven by four probes -- a
-- comment-only edit builds, three trivial lines do not). This file is required
-- by that widget, so it is loaded before anything can call this.
--
-- Returns the HP text so the widget's ONE modified line still does its old job:
--     self.player_hp:setText( CoD.TodAuraTint( self, hp ) )
-- and repaints the bar's tint as a side effect through TodHealthTint (red while
-- downed, white otherwise), so an HP-text refresh can never leave a stale tint.
function CoD.TodAuraTint( widget, hp )
	CoD.TodHealthTint.Paint( widget )
	return Engine.Localize( hp .. " HP" )
end
