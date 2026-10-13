// DEALER WEAPONS: finite, warned attacks. Appended to tod_dealer_finale by land.py.
// Warning footprints remain at the original positions. No pursuit during a cast;
// cover clips both the visual shot and its damage. No attack survives a phase flip.

// PURE: generation/phase/lifetime gate, shared by every warning/release/wait.
function dc_verdict( alive, phase, expected_phase, serial, expected_serial, paused, held )
{
	if ( !alive ) return "gone";
	if ( phase != expected_phase ) return "phase";
	if ( serial != expected_serial ) return "superseded";
	if ( IS_TRUE( paused ) ) return "pause";
	if ( IS_TRUE( held ) ) return "hold";
	return "ok";
}

// PURE: shock footprint matches the 100-unit warning ring, across stair heights.
function dc_in_shock( point, center )
{
	d = point - center;
	return ( d[ 0 ] * d[ 0 ] + d[ 1 ] * d[ 1 ] <= TOD_DC_RADIUS * TOD_DC_RADIUS && Abs( d[ 2 ] ) <= TOD_DC_HEIGHT );
}

// PURE: distance to the finite, cover-clipped bullet segment. Never the infinite line.
function dc_in_shot( point, start, finish )
{
	ab = finish - start;
	ap = point - start;
	length_sq = ab[ 0 ] * ab[ 0 ] + ab[ 1 ] * ab[ 1 ] + ab[ 2 ] * ab[ 2 ];
	if ( length_sq < 1 ) return false;
	t = ( ap[ 0 ] * ab[ 0 ] + ap[ 1 ] * ab[ 1 ] + ap[ 2 ] * ab[ 2 ] ) / length_sq;
	if ( t < 0 || t > 1 ) return false;
	closest = start + ab * t;
	return ( DistanceSquared( point, closest ) <= TOD_DC_SHOT_RADIUS * TOD_DC_SHOT_RADIUS );
}

function dc_target_ok( p )
{
	if ( !isdefined( p ) || !IsPlayer( p ) || !IsAlive( p ) ) return false;
	if ( !isdefined( p.sessionstate ) || p.sessionstate != "playing" ) return false;
	if ( IS_TRUE( p.ignoreme ) || IS_TRUE( p.tod_jumppad_flying ) || IS_TRUE( p.tod_spin_locked ) ) return false;
	if ( !( zm_utility::is_player_valid( p ) ) ) return false;
	if ( DistanceSquared( p.origin, self.origin ) > TOD_DC_RANGE * TOD_DC_RANGE ) return false;
	return true;
}

function dc_status( ctx )
{
	if ( !isdefined( self ) || !IsAlive( self ) ) return "gone";
	if ( self dc_disabled() ) return "stun";
	return dc_verdict( self.health > 0, self.tod_dealer_state, ctx.phase, self.tod_dealer_attack_serial, ctx.serial,
		level.tod_upgrade_pause, level.tod_dealer_hold );
}

function dc_disabled()
{
	now = GetTime();
	return ( IS_TRUE( self.tod_frozen ) || ( isdefined( self.tod_emp_until ) && self.tod_emp_until > now )
		|| ( isdefined( self.tod_stun_until ) && self.tod_stun_until > now ) );
}

function dc_wait( ctx, secs )
{
	until = GetTime() + int( secs * 1000 );
	while ( GetTime() < until )
	{
		if ( ( self dc_status( ctx ) ) != "ok" ) return false;
		wait TOD_DC_POLL;
	}
	return ( ( self dc_status( ctx ) ) == "ok" );
}

function dc_host( ctx, effect, org, angles, life )
{
	host = fx_carrier( effect, org, angles, life );
	if ( isdefined( host ) ) ctx.hosts[ ctx.hosts.size ] = host;
	return host;
}

function dc_cleanup( ctx, why )
{
	foreach ( h in ctx.hosts )
		if ( isdefined( h ) ) h Delete();
	ctx.hosts = [];
	foreach ( p in ctx.warned )
		if ( isdefined( p ) ) p StopLocalSound( ( ctx.kind == "shock" ? TOD_DC_SND_WARNING : TOD_DC_SND_BURST_TELL ) );
	ctx.warned = [];
	if ( !isdefined( self ) ) return;
	// A death/phase edge already reclaimed the lane: this old cast cannot restore its weapon.
	if ( self.tod_dealer_attack_serial != ctx.serial ) return;
	self.tod_dealer_attacking = false;
	self.tod_dealer_attack_ctx = undefined;
	if ( IsAlive( self ) )
	{
		self StopAnimScripted();
		self.ignoreall = ( IS_TRUE( level.tod_upgrade_pause ) || IS_TRUE( level.tod_dealer_hold ) || IS_TRUE( self.tod_frozen ) || ( self dc_disabled() ) );
		self weapon_set( ( self.tod_dealer_state == 1 ? "scythe" : "lmg" ) );
	}
	dev_log( "ATTACK_END gen=" + self.tod_dealer_gen + " op=" + ctx.serial + " kind=" + ctx.kind + " why=" + why + " hosts=0" );
}

function dc_cancel( why )
{
	if ( isdefined( self.tod_dealer_attack_ctx ) )
		self dc_cleanup( self.tod_dealer_attack_ctx, why );
	self.tod_dealer_attack_serial++;
}

function dc_begin( kind, target )
{
	ctx = SpawnStruct();
	self.tod_dealer_attack_serial++;
	ctx.serial = self.tod_dealer_attack_serial;
	ctx.phase = self.tod_dealer_state;
	ctx.kind = kind;
	ctx.hosts = [];
	ctx.warned = [];
	self.tod_dealer_attack_ctx = ctx;
	self.tod_dealer_attacking = true;
	self.ignoreall = true;
	self ClearPath();
	self SetGoal( self.origin, true );
	face = VectorToAngles( ( target.origin[ 0 ], target.origin[ 1 ], self.origin[ 2 ] ) - self.origin );
	self weapon_set( ( kind == "shock" ? "dg2" : "lmg" ) );
	clip = %tod_dealer_c_shock;
	if ( kind == "burst" ) clip = %tod_dealer_c_burst;
	self AnimScripted( "note_notify", self.origin, face, clip, "normal", undefined, 1.0, 0.1 );
	dev_log( "ATTACK_BEGIN gen=" + self.tod_dealer_gen + " op=" + ctx.serial + " kind=" + kind + " phase=" + ctx.phase + " target=" + target GetEntityNumber() );
	return ctx;
}

function dc_visible( from, to, p )
{
	trace = BulletTrace( from, to, false, self );
	return ( trace[ "fraction" ] == 1 );
}

function dc_damage( p, dmg, kind, at )
{
	if ( !( self dc_target_ok( p ) ) || IS_TRUE( level.tod_house_shield ) || IS_TRUE( level.tod_upgrade_pause ) || IS_TRUE( level.tod_dealer_hold ) ) return;
	mod = ( kind == "shock" ? "MOD_ELECTROCUTED" : "MOD_RIFLE_BULLET" );
	p DoDamage( dmg, at, self, self, undefined, mod, 0 );
	dev_log( "ATTACK_HIT gen=" + self.tod_dealer_gen + " kind=" + kind + " victim=" + p GetEntityNumber() + " damage=" + dmg );
}

// The donor's tag_flash in attached-model coordinates, measured by 18_combat_clips.py.
// BO3's AnglesToRight is -Y in model space (the native tag-offset convention).
function dc_muzzle()
{
	ang = self GetTagAngles( "tag_weapon_right" );
	off = TOD_DC_LMG_MUZZLE;
	base = self GetTagOrigin( "tag_weapon_right" );
	muzzle = ( base + AnglesToForward( ang ) * off[ 0 ]
		- AnglesToRight( ang ) * off[ 1 ] + AnglesToUp( ang ) * off[ 2 ] );
	barrel = BulletTrace( self.origin + ( 0, 0, 40 ), muzzle, false, self );
	if ( barrel[ "fraction" ] < 1 ) return undefined; // Never fire from the far side of cover.
	return muzzle;
}

function dc_shock( target )
{
	ctx = self dc_begin( "shock", target );
	points = [];
	// Lock at most four positions, once. Never track a player after showing the warning.
	foreach ( p in GetPlayers() )
	{
		if ( points.size >= TOD_DC_TARGET_MAX ) break;
		if ( !( self dc_target_ok( p ) ) ) continue;
		floor = BulletTrace( p.origin + ( 0, 0, 12 ), p.origin - ( 0, 0, 150 ), false, p );
		if ( floor[ "fraction" ] >= 1 ) continue;
		point = floor[ "position" ] + ( 0, 0, 3 );
		host = self dc_host( ctx, TOD_DC_FX_WARNING, point, ( 0, 0, 0 ), TOD_DC_SHOCK_TELL + 0.2 );
		if ( isdefined( host ) ) points[ points.size ] = point;
	}
	if ( points.size == 0 )
	{
		self dc_cleanup( ctx, "no_warning" );
		return;
	}
	coil = self dc_host( ctx, TOD_DC_FX_CHARGE, self tag_point( "tag_weapon_right", 60 ), self.angles, TOD_DC_SHOCK_TELL + 0.2 );
	if ( isdefined( coil ) ) coil LinkTo( self, "tag_weapon_right", ( 35, 0, 3 ), ( 0, 0, 0 ) );
	foreach ( p in GetPlayers() )
		if ( self dc_target_ok( p ) )
		{
			p PlaySoundToPlayer( TOD_DC_SND_WARNING, p );
			ctx.warned[ ctx.warned.size ] = p;
		}
	dev_log( "ATTACK_TELL gen=" + self.tod_dealer_gen + " op=" + ctx.serial + " kind=shock marks=" + points.size + " seconds=" + TOD_DC_SHOCK_TELL + " radius=" + TOD_DC_RADIUS );
	if ( !( self dc_wait( ctx, TOD_DC_SHOCK_TELL ) ) )
	{
		self dc_cleanup( ctx, self dc_status( ctx ) );
		return;
	}
	foreach ( h in ctx.hosts ) if ( isdefined( h ) ) h Delete();
	ctx.hosts = [];
	impacts = [];
	foreach ( point in points )
	{
		impact = self dc_host( ctx, TOD_DC_FX_SHOCK, point, ( 0, 0, 0 ), TOD_DC_SHOCK_LIFE );
		if ( !isdefined( impact ) ) continue;
		impacts[ impacts.size ] = point;
	}
	// Give the impact hosts their two replication frames; damage meets the visible discharge.
	if ( self dc_wait( ctx, TOD_DEALER_FX_REPLICATE ) )
	{
		// One weapon report, including co-op. Overlapping marks must not stack four identical cues.
		if ( impacts.size > 0 ) tod_perk_scatter::play_sound_at_origin( self tag_point( "tag_weapon_right", 60 ), TOD_DC_SND_SHOCK, 2 );
		foreach ( p in GetPlayers() )
		{
			if ( !( self dc_target_ok( p ) ) ) continue;
			foreach ( point in impacts )
			{
				if ( dc_in_shock( p.origin, point ) && self dc_visible( point + ( 0, 0, 20 ), p.origin + ( 0, 0, 35 ), p ) )
				{
					self dc_damage( p, TOD_DC_SHOCK_DAMAGE, "shock", point );
					break; // Overlapping co-op circles never multiply a player's shock damage.
				}
			}
		}
		dev_log( "ATTACK_FIRE gen=" + self.tod_dealer_gen + " op=" + ctx.serial + " kind=shock marks=" + points.size );
		self dc_wait( ctx, TOD_DC_RECOVERY );
	}
	why = self dc_status( ctx );
	self dc_cleanup( ctx, ( why == "ok" ? "complete" : why ) );
}

function dc_burst( target )
{
	ctx = self dc_begin( "burst", target );
	// The locked point, not a homing burst. A red danger ring and distinct audible rack precede it.
	aim = target.origin + ( 0, 0, 40 );
	center = target.origin + ( 0, 0, 3 );
	mark = self dc_host( ctx, TOD_DC_FX_WARNING, center, ( 0, 0, 0 ), TOD_DC_BURST_TELL + TOD_DC_BURST_SHOTS * TOD_DC_SHOT_GAP + 0.2 );
	if ( !isdefined( mark ) ) { self dc_cleanup( ctx, "no_warning" ); return; }
	foreach ( p in GetPlayers() )
		if ( self dc_target_ok( p ) )
		{
			p PlaySoundToPlayer( TOD_DC_SND_BURST_TELL, p );
			ctx.warned[ ctx.warned.size ] = p;
		}
	dev_log( "ATTACK_TELL gen=" + self.tod_dealer_gen + " op=" + ctx.serial + " kind=burst seconds=" + TOD_DC_BURST_TELL + " aim=" + aim );
	if ( !( self dc_wait( ctx, TOD_DC_BURST_TELL ) ) )
	{
		self dc_cleanup( ctx, self dc_status( ctx ) );
		return;
	}
	for ( shot = 0; shot < TOD_DC_BURST_SHOTS; shot++ )
	{
		if ( ( self dc_status( ctx ) ) != "ok" || !( self dc_target_ok( target ) ) ) break;
		muzzle = self dc_muzzle();
		if ( !isdefined( muzzle ) ) break;
		trace = BulletTrace( muzzle, aim, false, self );
		end = trace[ "position" ];
		self dc_host( ctx, TOD_DC_FX_MUZZLE, muzzle, VectorToAngles( end - muzzle ), 0.22 );
		bullet = self dc_host( ctx, TOD_DC_FX_TRACER, muzzle, VectorToAngles( end - muzzle ), 0.30 );
		if ( !isdefined( bullet ) ) break; // No invisible hit when the carrier pool is exhausted.
		if ( !( self dc_wait( ctx, TOD_DEALER_FX_REPLICATE ) ) ) break;
		tod_perk_scatter::play_sound_at_origin( muzzle, TOD_DC_SND_SHOT, 1 );
		if ( isdefined( bullet ) ) bullet MoveTo( end, TOD_DC_SHOT_TRAVEL );
		if ( !( self dc_wait( ctx, TOD_DC_SHOT_TRAVEL ) ) ) break;
		foreach ( p in GetPlayers() )
		{
			if ( !( self dc_target_ok( p ) ) ) continue;
			point = p.origin + ( 0, 0, 40 );
			if ( dc_in_shock( p.origin, center ) && dc_in_shot( point, muzzle, end ) && self dc_visible( muzzle, point, p ) )
				self dc_damage( p, TOD_DC_SHOT_DAMAGE, "burst", point );
		}
		self dc_wait( ctx, TOD_DC_SHOT_GAP - TOD_DEALER_FX_REPLICATE - TOD_DC_SHOT_TRAVEL );
	}
	dev_log( "ATTACK_FIRE gen=" + self.tod_dealer_gen + " op=" + ctx.serial + " kind=burst shots=" + shot );
	self dc_wait( ctx, TOD_DC_RECOVERY );
	why = self dc_status( ctx );
	self dc_cleanup( ctx, ( why == "ok" ? "complete" : why ) );
}

function combat()
{
	level endon( "end_game" );
	next = GetTime() + int( TOD_DC_OPENING_GRACE * 1000 );
	held_before = false;
	pick = 0;
	while ( isdefined( self ) && IsAlive( self ) )
	{
		wait TOD_DC_POLL;
		if ( !isdefined( self ) || !IsAlive( self ) ) break;
		blocked = ( IS_TRUE( level.tod_upgrade_pause ) || IS_TRUE( level.tod_dealer_hold ) || ( self dc_disabled() ) );
		if ( blocked ) { held_before = true; continue; }
		if ( held_before )
		{
			next = GetTime() + int( TOD_DC_OPENING_GRACE * 1000 );
			held_before = false;
		}
		if ( GetTime() < next ) continue;
		players = [];
		foreach ( p in GetPlayers() )
			if ( self dc_target_ok( p ) ) players[ players.size ] = p;
		if ( players.size == 0 ) continue;
		target = players[ pick % players.size ];
		pick++;
		if ( self.tod_dealer_state == 1 ) self dc_shock( target );
		else self dc_burst( target );
		if ( !isdefined( self ) || !IsAlive( self ) ) break;
		next = GetTime() + int( ( self.tod_dealer_state == 1 ? TOD_DC_SHOCK_GAP : TOD_DC_BURST_GAP ) * 1000 );
	}
	if ( isdefined( self ) ) self dc_cancel( "combat_over" );
}
