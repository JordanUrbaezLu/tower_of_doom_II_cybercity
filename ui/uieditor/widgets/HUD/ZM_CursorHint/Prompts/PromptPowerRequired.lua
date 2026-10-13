-- =============================================================================
-- PromptPowerRequired.lua — the refusal shown on a machine that has no power.
--
-- v19.3: REBUILT ON CoD.TodPromptCard, same as every other prompt card.
--
-- THIS CARD HAS NO FOOTER, DELIBERATELY. It is a refusal: there is nothing to
-- hold and nothing will happen. The kit's other cards all advertise a button,
-- and copying that here would tell the player to press something that does not
-- work. Build( { footer = false } ) is the one place that choice is expressed.
--
-- THE COPY WAS KIT FILLER. It read *"You must find and activate the power
-- first"* — grammatically fine, but it withholds the only thing the player
-- needs, which is WHERE, so the second line says so. If the switch ever moves,
-- this line moves with it.
-- W3E 2026-10-05: IT MOVED. Under THE FALL (docs/160, 164) the power is the
-- lever in the crown's POWER ROOM (the 1500 door off the hallway; _tod_fall
-- logs the plaza switch as "vestigial under DESCENT"), and every machine that
-- can refuse for power - the perks, the teleporters, the Black Market, the
-- jump pad - is met in the crown before it. "AT THE TOWER BASE" sent players
-- fifty floors the wrong way. The room's name is the one its door prompt shows.
-- =============================================================================

require( "ui.uieditor.widgets.HUD.ZM_CursorHint.Prompts.TodPromptCard" )

CoD.PromptPowerRequired = InheritFrom( LUI.UIElement )

function CoD.PromptPowerRequired.new( menu, controller )
	local self = LUI.UIElement.new()

	if PreLoadFunc then
		PreLoadFunc( self, controller )
	end

	self:setUseStencil( false )
	self:setClass( CoD.PromptPowerRequired )
	self.id = "PromptPowerRequired"
	self.soundSet = "HUD"
	self:setLeftRight( true, false, 0, 1280 )
	self:setTopBottom( true, false, 0, 720 )
	self:setAlpha( 0 )  -- start hidden

	CoD.TodPromptCard.Build( self, {
		icon   = "i_tod_prompt_icon_power",
		footer = false,
	} )

	CoD.TodPromptCard.SetTitle( self, "POWER REQUIRED" )
	CoD.TodPromptCard.SetDetail( self,
		"TURN ON THE POWER FIRST",
		"THE SWITCH IS IN THE POWER ROOM" )
	CoD.TodPromptCard.SetPrice( self, nil )
	CoD.TodPromptCard.SetLocked( self, true )

	if PostLoadFunc then
		PostLoadFunc( self, controller, menu )
	end

	return self
end
