#namespace tod_shop_timing;
// Generated from the authored Blender electrical timeline.
function power_bus( frame )
{
    v = 1;
    if ( frame >= 1 ) v = 1;
    if ( frame >= 31 ) v = 0;
    if ( frame >= 34 ) v = 1;
    if ( frame >= 36 ) v = 0;
    if ( frame >= 40 ) v = 1;
    if ( frame >= 91 ) v = 0;
    if ( frame >= 95 ) v = 1;
    if ( frame >= 98 ) v = 0;
    if ( frame >= 103 ) v = 1;
    if ( frame >= 151 ) v = 0;
    if ( frame >= 154 ) v = 1;
    if ( frame >= 157 ) v = 0;
    if ( frame >= 162 ) v = 1;
    if ( frame >= 181 ) v = 1;
    return v;
}
function letter( kind, frame )
{
    return power_bus( frame );
}
function events()
{
    a = [];
    a[ 0 ] = SpawnStruct();
    a[ 0 ].frame = 31;
    a[ 0 ].org = ( 42.95, -62.0, 110.5 );
    a[ 0 ].site = "sign T";
    a[ 0 ].sound = "tod_shop_spark_1";
    a[ 1 ] = SpawnStruct();
    a[ 1 ].frame = 31;
    a[ 1 ].org = ( -89, -23, 65 );
    a[ 1 ].site = "left core";
    a[ 1 ].sound = "";
    a[ 2 ] = SpawnStruct();
    a[ 2 ].frame = 31;
    a[ 2 ].org = ( 79, -27, 62 );
    a[ 2 ].site = "right core";
    a[ 2 ].sound = "";
    a[ 3 ] = SpawnStruct();
    a[ 3 ].frame = 91;
    a[ 3 ].org = ( 31.9, -62.0, 105.0 );
    a[ 3 ].site = "sign E";
    a[ 3 ].sound = "tod_shop_spark_2";
    a[ 4 ] = SpawnStruct();
    a[ 4 ].frame = 91;
    a[ 4 ].org = ( -89, -23, 34 );
    a[ 4 ].site = "left core";
    a[ 4 ].sound = "";
    a[ 5 ] = SpawnStruct();
    a[ 5 ].frame = 91;
    a[ 5 ].org = ( 81, -27, 36 );
    a[ 5 ].site = "right core";
    a[ 5 ].sound = "";
    a[ 6 ] = SpawnStruct();
    a[ 6 ].frame = 91;
    a[ 6 ].org = ( -41, -39, 51.5 );
    a[ 6 ].site = "counter left";
    a[ 6 ].sound = "";
    a[ 7 ] = SpawnStruct();
    a[ 7 ].frame = 151;
    a[ 7 ].org = ( -16.399, -62.0, 109.009 );
    a[ 7 ].site = "sign C";
    a[ 7 ].sound = "tod_shop_spark_3";
    a[ 8 ] = SpawnStruct();
    a[ 8 ].frame = 151;
    a[ 8 ].org = ( -89, -23, 65 );
    a[ 8 ].site = "left core";
    a[ 8 ].sound = "";
    a[ 9 ] = SpawnStruct();
    a[ 9 ].frame = 151;
    a[ 9 ].org = ( 79, -27, 62 );
    a[ 9 ].site = "right core";
    a[ 9 ].sound = "";
    return a;
}
