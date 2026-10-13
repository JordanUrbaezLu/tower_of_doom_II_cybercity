// tools/breacher/fixtures/bair_v1_20260929.gsc - THE NEGATIVE CONTROL for test_fusion_air.js, not shipped.
// The Breacher's air steering as built 2026-09-29: the drift and the turn ran together and fought (the
// user's logs: turned_deg 388..1859 in one Fusion launch against a 60-deg budget). The gate replays it on
// the same launch as the shipping function and requires it to SNAP, so the smoothness check can fail.
function breacher_air_steer()
{
	if ( !self can_act() || self IsMantling() || isdefined( self GetLinkedEnt() ) || self IsOnGround() )
	{
		if ( IS_TRUE( self.tod_bair_on ) )
		{
			self.tod_bair_on = undefined;
			dev_log( "BAIR_LAND player=" + self GetEntityNumber() + " air_ms=" + ( GetTime() - self.tod_bair_t0 ) + " turned_deg=" + Int( self.tod_bair_turned ) + " drift_peak=" + Int( self.tod_bair_drift_peak ) );
		}
		self.tod_bair_ref = 0;
		return;
	}
	if ( !IS_TRUE( self.tod_bair_on ) )
	{
		self.tod_bair_on = true;
		self.tod_bair_t0 = GetTime();
		self.tod_bair_turned = 0;
		self.tod_bair_drift_peak = 0;
		self.tod_bair_ref = 0;
		self.tod_bair_cap = TOD_BAIR_CAP_FLOOR;
		self.tod_bair_yaw = 0;
		dev_log( "BAIR_START player=" + self GetEntityNumber() + " speed=" + Int( Length( self GetVelocity() ) ) + ( IS_TRUE( self.tod_fjump_air ) ? " fusion_launch=1" : "" ) );
	}
	if ( !isdefined( self.tod_bair_anchor_ms ) ) self.tod_bair_anchor_ms = 0;
	v = self GetVelocity();
	out_x = v[ 0 ];
	out_y = v[ 1 ];
	dirty = false;
	fwd_in = 0;
	right_in = 0;
	m = self GetNormalizedMovement();
	if ( isdefined( m ) )
	{
		fwd_in = m[ 0 ];
		right_in = m[ 1 ] * TOD_BAIR_RIGHT_SIGN;
	}
	yaw = self GetPlayerAngles()[ 1 ];
	f = AnglesToForward( ( 0, yaw, 0 ) );
	r = AnglesToRight( ( 0, yaw, 0 ) );

	// THE ANCHOR is the flight the engine hands us, BEFORE this tick's lanes touch it: the
	// take-off heading and speed (map 1's rule), re-taken on an outside push (x REANCHOR) or a
	// Fusion launch - or the launch's push would be trimmed straight back to the old speed.
	sp0 = Sqrt( ( out_x * out_x ) + ( out_y * out_y ) );
	relaunch = ( isdefined( self.tod_fjump_launch_ms ) && self.tod_fjump_launch_ms > self.tod_bair_anchor_ms );
	if ( sp0 > 1 && ( self.tod_bair_ref <= 0 || sp0 > ( self.tod_bair_cap * TOD_BAIR_REANCHOR ) || relaunch ) )
	{
		self.tod_bair_yaw = VectorToAngles( ( out_x, out_y, 0 ) )[ 1 ];
		self.tod_bair_ref = sp0;
		self.tod_bair_cap = sp0;
		if ( self.tod_bair_cap < TOD_BAIR_CAP_FLOOR ) self.tod_bair_cap = TOD_BAIR_CAP_FLOOR;
		self.tod_bair_anchor_ms = GetTime();
	}

	// THE DRIFT: accelerate toward the stick, never past DRIFT along it
	mag = Sqrt( ( fwd_in * fwd_in ) + ( right_in * right_in ) );
	if ( mag >= TOD_BAIR_DEADZONE )
	{
		if ( mag > 1 ) mag = 1;
		wx = ( f[ 0 ] * fwd_in ) + ( r[ 0 ] * right_in );
		wy = ( f[ 1 ] * fwd_in ) + ( r[ 1 ] * right_in );
		wl = Sqrt( ( wx * wx ) + ( wy * wy ) );
		if ( wl > 0.001 )
		{
			wx = wx / wl;
			wy = wy / wl;
			add = ( TOD_BAIR_DRIFT * mag ) - ( ( out_x * wx ) + ( out_y * wy ) );
			if ( add > 0 )
			{
				acc = TOD_BAIR_DRIFT_ACCEL * TOD_KIT_TICK;
				if ( acc > add ) acc = add;
				out_x = out_x + ( wx * acc );
				out_y = out_y + ( wy * acc );
				dirty = true;
				drift = ( out_x * wx ) + ( out_y * wy );
				if ( drift > self.tod_bair_drift_peak ) self.tod_bair_drift_peak = drift;
			}
		}
	}

	// THE TURN: map 1's ATHLETE lane 4 (strafe only), budget + cone
	sp = Sqrt( ( out_x * out_x ) + ( out_y * out_y ) );
	if ( sp > 1 && self.tod_bair_ref > 0 )
	{
		c_yaw = VectorToAngles( ( out_x, out_y, 0 ) )[ 1 ];
		strafe = Abs( right_in );
		if ( strafe >= TOD_BAIR_DEADZONE )
		{
			if ( strafe > 1 ) strafe = 1;
			w_yaw = VectorToAngles( ( r[ 0 ] * right_in, r[ 1 ] * right_in, 0 ) )[ 1 ];
			gap = AngleClamp180( w_yaw - c_yaw );
			if ( Abs( gap ) >= TOD_BAIR_DEADBAND )
			{
				step_max = TOD_BAIR_TURN * strafe * TOD_KIT_TICK;
				ease = Abs( gap ) * TOD_BAIR_EASE;
				if ( step_max > ease ) step_max = ease;
				step = gap;
				if ( step > step_max ) step = step_max;
				else if ( step < ( 0 - step_max ) ) step = 0 - step_max;
				cur_dev = AngleClamp180( c_yaw - self.tod_bair_yaw );
				new_dev = cur_dev + step;
				if ( new_dev > TOD_BAIR_BUDGET ) step = TOD_BAIR_BUDGET - cur_dev;
				else if ( new_dev < ( 0 - TOD_BAIR_BUDGET ) ) step = ( 0 - TOD_BAIR_BUDGET ) - cur_dev;
				if ( Abs( step ) > 0.05 )
				{
					c_yaw = c_yaw + step;
					nf = AnglesToForward( ( 0, c_yaw, 0 ) );
					out_x = nf[ 0 ] * sp;
					out_y = nf[ 1 ] * sp;
					self.tod_bair_turned = self.tod_bair_turned + Abs( step );
					dirty = true;
				}
			}
		}
		// THE CONE: past 90 deg off the take-off line the speed cap shrinks toward REVERSE_KEEP
		dev = Abs( AngleClamp180( c_yaw - self.tod_bair_yaw ) );
		keep = 1;
		if ( dev > 90 )
		{
			t = ( dev - 90 ) / 90;
			if ( t > 1 ) t = 1;
			keep = 1 - ( t * ( 1 - TOD_BAIR_REVERSE_KEEP ) );
		}
		cap = self.tod_bair_ref * keep;
		if ( cap < TOD_BAIR_CAP_FLOOR ) cap = TOD_BAIR_CAP_FLOOR;
		self.tod_bair_cap = cap;
		if ( sp > cap )
		{
			out_x = out_x * cap / sp;
			out_y = out_y * cap / sp;
			dirty = true;
		}
	}
	if ( dirty )
		self SetVelocity( ( out_x, out_y, v[ 2 ] ) );
}
