// _tod_keeper.gsc — THE KEEPER'S ARCHETYPE HALF, which THE DEALER runs on.
//
// THE KEEPER BOSS IS RETIRED WHOLE (2026-10-05, W2E; user: "Just dont include
// assets not on this map in the build"). He was the Battle Arena's level-10
// boss wave (docs/186), but TOD_ARENA_HOUSE sent level 10 to the Dealer's House
// (docs/207) and that is now the only path: his spawn, his soul lines, his brain,
// his dissolve, his two actor clientfields, his client half (_tod_keeper.csc)
// and his zone lines are in archive/map1_carryover/.
//
// WHAT IS LEFT. The Dealer (_tod_dealer_finale.gsc) is the Keeper's skeleton
// and the Keeper's tree, so he registers these two on his own "dealer"
// archetype: the blackboard (the attributes his behaviour tree reads) and the
// zombie flags stock's services expect. They stay here, under the same names,
// so the Dealer's file needs no change. The Keeper's installed SOURCES stay too
// (tools/dealer_boss/install.py derives the Dealer from them; install_keeper.py
// --check pins them); none of the Keeper's own body, effects or unused clips is
// zoned any more.

#using scripts\shared\aat_shared;
#using scripts\shared\ai_shared;
#using scripts\shared\ai\archetype_utility;
#using scripts\shared\ai\systems\ai_interface;
#using scripts\shared\ai\systems\blackboard;
#using scripts\zm\_zm;
#using scripts\zm\_zm_spawner;

#insert scripts\shared\shared.gsh;

#namespace tod_keeper;

// ---------------------------------------------------------------------------
// THE ARCHETYPE (the pack's keeper script, kept to what the tree reads).
// PUBLIC: _tod_dealer_finale registers both on spawner archetype "dealer".
// ---------------------------------------------------------------------------
function keeper_blackboard()
{
	Blackboard::CreateBlackBoardForEntity( self );
	self AiUtility::RegisterUtilityBlackboardAttributes();
	ai::CreateInterfaceForEntity( self );
	Blackboard::RegisterBlackBoardAttribute( self, "_arms_position", "arms_up", &bb_arms_position );
	Blackboard::RegisterBlackBoardAttribute( self, "_locomotion_speed", "locomotion_speed_walk", &bb_locomotion_speed );
	Blackboard::RegisterBlackBoardAttribute( self, "_has_legs", "has_legs_yes", &bb_has_legs );
	Blackboard::RegisterBlackBoardAttribute( self, "_variant_type", 0, &bb_variant_type );
	Blackboard::RegisterBlackBoardAttribute( self, "_which_board_pull", undefined, undefined );
	Blackboard::RegisterBlackBoardAttribute( self, "_board_attack_spot", undefined, undefined );
	Blackboard::RegisterBlackBoardAttribute( self, "_grapple_direction", undefined, undefined );
	Blackboard::RegisterBlackBoardAttribute( self, "_locomotion_should_turn", "should_not_turn", &bb_should_turn );
	Blackboard::RegisterBlackBoardAttribute( self, "_idgun_damage_direction", "back", &bb_idgun_direction );
	Blackboard::RegisterBlackBoardAttribute( self, "_low_gravity_variant", 0, &bb_low_gravity );
	Blackboard::RegisterBlackBoardAttribute( self, "_knockdown_direction", undefined, undefined );
	Blackboard::RegisterBlackBoardAttribute( self, "_knockdown_type", undefined, undefined );
	self.___ArchetypeOnAnimscriptedCallback = &on_animscripted;
}

function private on_animscripted( entity )
{
	entity.__blackboard = undefined;
	entity keeper_blackboard();
}

function keeper_zombie_flags()
{
	self thread zm::update_zone_name();
	if ( isdefined( level.aat ) )
		self aat::aat_cooldown_init();   // AATs are off in this map (zm_cwpap); guarded so they can come back
	self thread zm_spawner::enemy_death_detection();
	self.completed_emerging_into_playable_area = true;
	self.is_zombie = true;
}

function bb_arms_position()
{
	if ( isdefined( self.zombie_arms_position ) && self.zombie_arms_position != "up" )
		return "arms_down";
	return "arms_up";
}

function bb_locomotion_speed()
{
	if ( isdefined( self.zombie_move_speed ) )
	{
		switch ( self.zombie_move_speed )
		{
			case "run":          return "locomotion_speed_run";
			case "sprint":       return "locomotion_speed_sprint";
			case "super_sprint": return "locomotion_speed_super_sprint";
		}
	}
	return "locomotion_speed_walk";
}

function bb_has_legs()
{
	if ( IS_TRUE( self.missinglegs ) )
		return "has_legs_no";
	return "has_legs_yes";
}

function bb_variant_type()
{
	if ( isdefined( self.variant_type ) )
		return self.variant_type;
	return 0;
}

function bb_should_turn()
{
	if ( IS_TRUE( self.should_turn ) )
		return "should_turn";
	return "should_not_turn";
}

function bb_idgun_direction()
{
	if ( isdefined( self.damage_direction ) )
		return self.damage_direction;
	return self AiUtility::BB_GetDamageDirection();
}

function bb_low_gravity()
{
	if ( isdefined( self.low_gravity_variant ) )
		return self.low_gravity_variant;
	return 0;
}
