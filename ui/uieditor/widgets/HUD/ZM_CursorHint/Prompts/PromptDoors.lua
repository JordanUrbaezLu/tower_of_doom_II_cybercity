-- =============================================================================
-- PromptDoors.lua — every buyable door and debris clear.
--
-- v19.3: REBUILT ON CoD.TodPromptCard. The chassis, icon, typeface, footer and
-- price lockup all come from the shared owner now; this file keeps ONLY its
-- parsing, which is the one thing genuinely specific to a door.
--
-- THREE PLAYER-FACING FIXES IN THIS PASS
--
--   1. THE TYPEFACE. Title was orbitron, detail and price ltromatic — the
--      vendored kit's fonts. All three are the map's own typeface now.
--
--   2. THE ARTICLE. _tod_doors.gsc writes "Open Door to the Teleport Bay", and
--      this card put the destination in the title VERBATIM, so the title band
--      read "the Teleport Bay" — lowercase article and all. Every other title
--      in this map is a bare noun (AMMO CRATE, TELEPORTER, POWER SWITCH), so
--      the leading article is stripped HERE rather than in the hint: the hint
--      still has to read as a sentence, the title does not.
--
--   3. THE DESCRIPTION SAID NOTHING. All 53 doors read *"Buy to unlock new
--      areas"* — kit copy that is true of every door in every map ever made.
--      The destination is already known by the time that line is written, so
--      it now says what is actually through the door.
--
-- ⚠️ THE PARSE DEPENDS ON THE HINT FORMAT "Open Door to <dest> ^2[Cost: N]".
-- Keep _tod_doors.gsc::spawn_buy_trigger EXACT or the title silently falls back.
-- =============================================================================

require( "ui.uieditor.widgets.HUD.ZM_CursorHint.Prompts.TodPromptCard" )

CoD.PromptDoors = InheritFrom( LUI.UIElement )

function CoD.PromptDoors.SetFooter( self, verb )
	CoD.TodPromptCard.SetFooter( self, verb )
end

-- WHAT IS THROUGH THE DOOR. Matched on the lowercased destination, first match
-- wins. A destination with no row gets the generic line, which is correct for
-- every spiral door - they are the rule, not the exception.
-- W3E 2026-10-05: THE TOWER IS A DESCENT NOW (docs/160). The Map One rows said
-- "CLIMB HIGHER INTO THE TOWER" on every one of the 26 paid doors (all of which
-- lead DOWN), "THE FINAL CLIMB BEGINS HERE" / "PACK-A-PUNCH IS UP HERE" for
-- destinations that no longer exist, and the crown's Teleporter door fell
-- through to the climb line ("teleport bay" never matched "the Teleporter").
-- Destinations are generated (tools/gen_tower_map.js -> _tod_door_data.gsc):
-- the Power Room (crown 1500 + base 750, a switch in each), the Teleporter
-- (the crown room whose pad goes down to the base), the Causeway (the 5000
-- gate out of the crown hall), the four Workshops, the Conduit, the Tower
-- Plaza, the Ground Floor and "the Spiral - Floor N".
local DEST_DETAIL = {
	{ "power room",  "THE POWER SWITCH IS INSIDE" },
	{ "teleporter",  "THE TELEPORTER TO THE BASE" },
	{ "causeway",    "THE WAY OUT OF THE CROWN" },
	{ "workshop",    "A SIDE WING OF THE BASE" },
}
local DEST_DETAIL_DEFAULT = "FURTHER DOWN THE TOWER"

-- Articles are stripped from the TITLE only. "the Spiral - Floor 41" is correct
-- English inside the hint sentence and wrong as a title band.
local function titleFor( dest )
	local t = string.gsub( dest, "^[Tt][Hh][Ee]%s+", "" )
	return t
end

local function detailFor( dest )
	local d = string.lower( dest )
	for i = 1, #DEST_DETAIL do
		if string.find( d, DEST_DETAIL[ i ][ 1 ], 1, true ) then
			return DEST_DETAIL[ i ][ 2 ]
		end
	end
	return DEST_DETAIL_DEFAULT
end

function CoD.PromptDoors.new( menu, controller )
	local self = LUI.UIElement.new()

	if PreLoadFunc then
		PreLoadFunc( self, controller )
	end

	self:setUseStencil( false )
	self:setClass( CoD.PromptDoors )
	self.id = "PromptDoors"
	self.soundSet = "HUD"
	self:setLeftRight( true, false, 0, 1280 )
	self:setTopBottom( true, false, 0, 720 )
	self:setAlpha( 0 )  -- start hidden

	CoD.TodPromptCard.Build( self, {
		icon   = "i_tod_prompt_icon_door",
		footer = "OPEN",
	} )

	CoD.TodPromptCard.SetTitle( self, "LOCKED AREA" )
	CoD.TodPromptCard.SetDetail( self, DEST_DETAIL_DEFAULT, "" )

	self:subscribeToModel( Engine.GetModel( Engine.GetModelForController( controller ), "hudItems.cursorHintText" ), function ( model )
		local hintText = Engine.GetModelValue( model )
		if not hintText or hintText == "" then
			return
		end

		local h = string.lower( hintText )
		local isDebris = string.find( h, "debris" ) or string.find( h, "clear" )

		-- THE SEALED WAY DOWN (2026-10-04, _tod_doors.gsc haven_seal_watch): a haven
		-- floor's door while its dome is not yet secured. Nothing to hold and nothing to
		-- pay, so no footer and no price, and the locked frame; the next normal door
		-- prompt puts all three back (this card is reused for every door).
		if string.find( h, "sealed", 1, true ) then
			CoD.TodPromptCard.SetTitle( self, "SEALED" )
			CoD.TodPromptCard.SetDetail( self, "SECURE THE DOME", "ON THIS FLOOR FIRST" )
			CoD.TodPromptCard.SetPrice( self, nil )
			CoD.TodPromptCard.SetFooterVisible( self, false )
			CoD.TodPromptCard.SetLocked( self, true )
			return
		end
		CoD.TodPromptCard.SetLocked( self, false )
		CoD.TodPromptCard.SetFooterVisible( self, true )

		-- PRICE. Both spellings, because the bracketed form is this map's and
		-- the bare form is stock's.
		local cost = string.match( hintText, "%[[Cc]ost:%s*(%d+)%]" )
		          or string.match( hintText, "[Cc]ost:%s*(%d+)" )
		CoD.TodPromptCard.SetPrice( self, cost )

		-- DESTINATION. Colour codes are stripped first: the glyph sheet has no
		-- caret, so a stray ^2 would be dropped mid-string and shift the rest.
		local dest = string.match( hintText, "[Oo]pen [Dd]oor to%s+(.-)%s*%^%d*%[[Cc]ost" )
		          or string.match( hintText, "[Oo]pen [Dd]oor to%s+(.-)%s*%[[Cc]ost" )
		          or string.match( hintText, "[Oo]pen [Dd]oor to%s+(.+)" )

		if dest then
			dest = CoD.TodPromptCard.StripColour( dest )
			dest = string.gsub( dest, "^%s*(.-)%s*$", "%1" )
		end

		if isDebris then
			CoD.TodPromptCard.SetTitle( self, dest and dest ~= "" and titleFor( dest ) or "BLOCKED PATH" )
			CoD.TodPromptCard.SetDetail( self, "CLEAR THE WAY THROUGH", "" )
			CoD.TodPromptCard.SetFooter( self, "CLEAR" )
			return
		end

		if dest and dest ~= "" then
			CoD.TodPromptCard.SetTitle( self, titleFor( dest ) )
			CoD.TodPromptCard.SetDetail( self, detailFor( dest ), "" )
		else
			CoD.TodPromptCard.SetTitle( self, "LOCKED AREA" )
			CoD.TodPromptCard.SetDetail( self, DEST_DETAIL_DEFAULT, "" )
		end
		CoD.TodPromptCard.SetFooter( self, "OPEN" )
	end )

	if PostLoadFunc then
		PostLoadFunc( self, controller, menu )
	end

	return self
end
