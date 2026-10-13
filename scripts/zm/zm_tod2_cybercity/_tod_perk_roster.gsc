// STAGED: shared, explicit sellable roster. No physical-machine dependency.
#using scripts\zm\_zm_perks;
#using scripts\zm\_zm_utility;
#insert scripts\shared\shared.gsh;
#namespace tod_perk_roster;

function keys()
{
    return array( "specialty_armorvest", "specialty_fastreload", "specialty_quickrevive",
        "specialty_staminup", "specialty_widowswine", "specialty_combat_efficiency",
        "specialty_doubletap2", "specialty_nomotionsensor", "specialty_electriccherry" );
}

function perk_for_id( id )
{
    if ( !isdefined( id ) || id < 1 || id > 9 || int( id ) != id ) return undefined;
    all = keys();
    return all[ id - 1 ];
}

function owns( p, perk )
{
    return ( p HasPerk( perk ) || p zm_perks::has_perk_paused( perk ) );
}

function owned_count( p )
{
    n = 0;
    all = keys();
    foreach ( perk in all ) if ( owns( p, perk ) ) n++;
    return n;
}

function owned_mask( p )
{
    mask = 0;
    bit = 1;
    all = keys();
    foreach ( perk in all )
    {
        if ( owns( p, perk ) ) mask += bit;
        bit *= 2;
    }
    return mask;
}

function registered( perk )
{
    return ( isdefined( perk ) && isdefined( level._custom_perks ) && isdefined( level._custom_perks[ perk ] ) );
}

function pending( p, perk )
{
    return ( isdefined( p.perk_purchased ) && p.perk_purchased == perk );
}

function free_pool( p )
{
    pool = [];
    if ( !( p zm_utility::can_player_purchase_perk() ) ) return pool;
    all = keys();
    foreach ( perk in all )
        if ( registered( perk ) && !owns( p, perk ) && !pending( p, perk ) ) pool[ pool.size ] = perk;
    return pool;
}

// The free bottle's existing solo Quick Revive exemption is retained. Paid
// Wunderfizz purchases never write this flag and keep stock's three-use ledger.
function give_random( p )
{
    pool = free_pool( p );
    if ( pool.size == 0 ) return undefined;
    perk = pool[ RandomInt( pool.size ) ];
    if ( perk == "specialty_quickrevive" && zm_perks::use_solo_revive() )
        level.solo_game_free_player_quickrevive = true;
    p zm_perks::give_perk( perk, false );
    return perk;
}
