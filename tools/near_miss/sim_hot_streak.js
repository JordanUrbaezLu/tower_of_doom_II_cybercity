// tools/near_miss/sim_hot_streak.js — docs/201 section 5: what THE HOT STREAK does over whole runs.
//
// A PLANNING TOOL (2026-10-02). It models the docs/187 card odds and the docs/188 spin odds, their
// luck guarantees, and the proposed streak rule. It does NOT read the shipping scripts: once the
// feature is built, tools/test_hot_streak.js runs the shipping functions instead (docs/201 section 7).
//
//   node tools/near_miss/sim_hot_streak.js                          every rule x strength variant
//   node tools/near_miss/sim_hot_streak.js --mult 1.15,1.30,1.50    one strength (heat 1 / 2 / 3)
//   node tools/near_miss/sim_hot_streak.js --runs 50000 --seed 9
//
// THE RUN MODEL is an assumption; change it here and quote the new numbers, never the other way round:
//   12 card deals (round 1, then every 4 rounds); the bar before a deal is U(30,100) with a 25% chance
//   it is full; the first deal is at bar 0 (and floored at RARE); after each deal a 60% chance of one
//   Black Market spin at bar U(0,60); a 15% chance per interval of going down (which ends the streak).
//
// THE RULES compared:
//   heat     the first idea: EPIC +1 / LEGENDARY +2 heat, a miss -1. REJECTED: hot on ~55% of pulls.
//   shown    the pick: a STREAK of pulls with an EPIC+ result as the player sees it (a guaranteed card
//            counts), LEGENDARY counts 2; anything less or a down ends it; heat = streak - 1, max 3.
//   dice     the same streak, but only results the dice gave count (a guarantee's promotion does not).
'use strict';

const args = process.argv.slice(2);
const opt = ( name, def ) => { const i = args.indexOf( '--' + name ); return i >= 0 ? args[ i + 1 ] : def; };
const RUNS = parseInt( opt( 'runs', '200000' ), 10 );
const SEED = parseInt( opt( 'seed', '777' ), 10 );

let state = SEED;
function rnd() {   // mulberry32: exact 32-bit integer math (a naive LCG loses bits past 2^53 in JS)
	state = ( state + 0x6D2B79F5 ) | 0;
	let t = state;
	t = Math.imul( t ^ ( t >>> 15 ), t | 1 );
	t ^= t + Math.imul( t ^ ( t >>> 7 ), t | 61 );
	return ( ( t ^ ( t >>> 14 ) ) >>> 0 ) / 4294967296;
}

// docs/187 section 2: a straight line from 56/27/13/4 (empty bar) to 36/36/20/8 (full). Heat multiplies
// the EPIC and LEGENDARY slices; COMMON pays for it.
function slices( bar, heat, mult ) {
	const t = Math.max( 0, Math.min( 1, bar / 100 ) );
	let c = 56 - 20 * t;
	const r = 27 + 9 * t, e = ( 13 + 7 * t ) * mult[ heat ], l = ( 4 + 4 * t ) * mult[ heat ];
	c = 100 - r - e - l;
	if ( c < 0 ) throw new Error( 'COMMON below 0 at bar ' + bar + ' heat ' + heat );
	return [ c, r, e, l ];
}
function roll( s ) {   // 0 COMMON .. 3 LEGENDARY
	const x = rnd() * 100;
	if ( x < s[ 3 ] ) return 3;
	if ( x < s[ 3 ] + s[ 2 ] ) return 2;
	if ( x < s[ 3 ] + s[ 2 ] + s[ 1 ] ) return 1;
	return 0;
}
// A card deal: two cards; a full bar floors one at EPIC (25% of those LEGENDARY), half a bar at RARE,
// the first deal at RARE (_tod_upgrades guarantee_rarity).
function deal( bar, heat, mult, first ) {
	const s = slices( bar, heat, mult ), a = [ roll( s ), roll( s ) ];
	const dice = Math.max( a[ 0 ], a[ 1 ] );
	let want = bar >= 100 ? 2 : bar >= 50 ? 1 : 0;
	if ( first && want < 1 ) want = 1;
	if ( want > 0 && dice < want ) {
		const i = a[ 0 ] <= a[ 1 ] ? 0 : 1;
		a[ i ] = ( want === 2 && rnd() < 0.25 ) ? 3 : want;
	}
	return { shown: Math.max( a[ 0 ], a[ 1 ] ), dice, legs: a.filter( x => x === 3 ).length };
}
// A spin: one prize; 50+ luck lifts COMMON to RARE, 100 lifts COMMON / RARE to EPIC (25% LEGENDARY)
// (_tod_shop roll_rarity).
function spin( bar, heat, mult ) {
	const dice = roll( slices( bar, heat, mult ) );
	let r = dice;
	if ( bar >= 100 && r < 2 ) r = rnd() < 0.25 ? 3 : 2;
	else if ( bar >= 50 && r < 1 ) r = 1;
	return { shown: r, dice, legs: r === 3 ? 1 : 0 };
}

const RULES = {
	heat: ( st, o ) => {
		const b = o.shown;
		st.heat = b === 3 ? Math.min( 3, st.heat + 2 ) : b === 2 ? Math.min( 3, st.heat + 1 ) : Math.max( 0, st.heat - 1 );
	},
	shown: ( st, o ) => {
		const b = o.shown;
		st.streak = b >= 2 ? st.streak + ( b === 3 ? 2 : 1 ) : 0;
		st.heat = Math.max( 0, Math.min( 3, st.streak - 1 ) );
	},
	dice: ( st, o ) => {
		const b = o.dice;
		st.streak = b >= 2 ? st.streak + ( b === 3 ? 2 : 1 ) : 0;
		st.heat = Math.max( 0, Math.min( 3, st.streak - 1 ) );
	},
};

function run( rule, mult ) {
	const st = { streak: 0, heat: 0 };
	const o = { legs: 0, pulls: 0, hot: 0, fire: 0, firePulls: 0 };
	const pull = res => {
		o.legs += res.legs;
		o.pulls++;
		rule( st, res );
		if ( st.heat === 3 ) o.fire = 1;
	};
	const before = () => { if ( st.heat > 0 ) o.hot++; if ( st.heat === 3 ) o.firePulls++; };
	for ( let d = 0; d < 12; d++ ) {
		const bar = d === 0 ? 0 : ( rnd() < 0.25 ? 100 : 30 + rnd() * 70 );
		before();
		pull( deal( bar, st.heat, mult, d === 0 ) );
		if ( rnd() < 0.6 ) {
			before();
			pull( spin( rnd() * 60, st.heat, mult ) );
		}
		if ( rnd() < 0.15 ) { st.streak = 0; st.heat = 0; }
	}
	return o;
}

function report( ruleName, multName, mult ) {
	state = SEED;
	const legs = [];
	let fire = 0, hot = 0, firePulls = 0, pulls = 0;
	for ( let i = 0; i < RUNS; i++ ) {
		const o = run( RULES[ ruleName ], mult );
		legs.push( o.legs );
		fire += o.fire; hot += o.hot; firePulls += o.firePulls; pulls += o.pulls;
	}
	const mean = legs.reduce( ( x, y ) => x + y, 0 ) / RUNS;
	const share = k => ( 100 * legs.filter( x => x >= k ).length / RUNS ).toFixed( 1 ).padStart( 4 );
	console.log( `${ ruleName.padEnd( 5 ) } ${ multName.padEnd( 24 ) } | LEGENDARY/run ${ mean.toFixed( 2 ) } | runs with 4+ ${ share( 4 ) }%  6+ ${ share( 6 ) }%`
		+ ` | pulls made while hot ${ ( 100 * hot / pulls ).toFixed( 1 ).padStart( 4 ) }%  ON FIRE ${ ( 100 * firePulls / pulls ).toFixed( 1 ).padStart( 4 ) }%`
		+ ` | runs that reach ON FIRE ${ ( 100 * fire / RUNS ).toFixed( 1 ).padStart( 4 ) }%` );
}

const STRENGTHS = {
	'off (display only)': [ 1, 1, 1, 1 ],
	'mild 1.10/1.20/1.35': [ 1, 1.10, 1.20, 1.35 ],
	'pick 1.15/1.30/1.50': [ 1, 1.15, 1.30, 1.50 ],
	'strong 1.25/1.50/1.80': [ 1, 1.25, 1.50, 1.80 ],
};
const one = opt( 'mult', null );
if ( one ) {
	const m = one.split( ',' ).map( Number );
	if ( m.length !== 3 || m.some( x => !( x >= 1 ) ) ) throw new Error( '--mult wants three numbers >= 1, e.g. 1.15,1.30,1.50' );
	for ( const r of Object.keys( RULES ) ) report( r, one, [ 1, ...m ] );
} else {
	for ( const r of Object.keys( RULES ) )
		for ( const [ name, m ] of Object.entries( STRENGTHS ) ) report( r, name, m );
}

// The odds a card or a spin rolls at each heat (before the guarantees), for docs/201's table.
const pick = one ? [ 1, ...one.split( ',' ).map( Number ) ] : STRENGTHS[ 'pick 1.15/1.30/1.50' ];
console.log( '\nodds by heat (C / R / E / L, EPIC+), ' + pick.slice( 1 ).join( '/' ) );
for ( const bar of [ 0, 50, 100 ] ) {
	const row = [];
	for ( let h = 0; h <= 3; h++ ) {
		const s = slices( bar, h, pick );
		row.push( `h${ h } ${ s.map( x => x.toFixed( 1 ) ).join( '/' ) } (${ ( s[ 2 ] + s[ 3 ] ).toFixed( 1 ) })` );
	}
	console.log( `bar ${ String( bar ).padStart( 3 ) }: ` + row.join( '  ' ) );
}
