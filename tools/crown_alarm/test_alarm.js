// Exercise the shipping GSC state transitions, including seal during replication.
const fs=require('fs'),assert=require('assert/strict');
const code=fs.readFileSync('scripts/zm/zm_tod2_cybercity/_tod_crown_alarm.gsc','utf8');
const body=name=>code.match(new RegExp('function '+name+'\\([^)]*\\)\\s*\\{([\\s\\S]*?)\\n\\}'))[1];
const onModel=new Function('kind',body('on_model'));
const isHigh=new Function('kind',body('is_high'));
const offModel=new Function('kind','is_high',body('off_model'));
const housingModel=new Function('kind','is_high',body('housing_model'));
const fall=fs.readFileSync('scripts/zm/zm_tod2_cybercity/_tod_fall.gsc','utf8');
const importAt=fall.indexOf('#using scripts\\zm\\zm_tod2_cybercity\\_tod_crown_alarm;');
assert(importAt>=0&&importAt<fall.indexOf('#precache('),'BO3 imports must precede precache directives');
const mounts=JSON.parse(fs.readFileSync('art/crown_alarm/mounts.json','utf8'));
assert.equal(mounts.length,30);
for(const [kind,n] of Object.entries({pillar:12,pendant:1,point:16,apex:1}))assert.equal(mounts.filter(x=>x.kind===kind).length,n);
assert.equal(new Set(mounts.map(x=>x.org.join(','))).size,30);
// Every mount must touch a real emitted solid, not merely agree with a table.
const solids=JSON.parse(fs.readFileSync('art/cybercity_materials/crown_inventory.json','utf8')).rows;
function supported(m){
 const [x,y,z]=m.org,inverted=m.kind==='pendant',r=inverted?0:26*m.scale;
 return solids.some(s=>x-r>=s.lo[0]-.01&&x+r<=s.hi[0]+.01&&y-r>=s.lo[1]-.01&&y+r<=s.hi[1]+.01&&
  Math.abs((inverted?s.lo[2]:s.hi[2])-z)<.01&&s.faces.some(f=>Math.abs(f.n[2]-(inverted?-1:1))<.001&&Math.abs(f.d-f.n[2]*z)<.01));
}
assert(mounts.every(supported),'a fixture floats above or intersects its mounting solid');
assert(!supported({...mounts[0],org:[...mounts[0].org.slice(0,2),mounts[0].org[2]+32]}),'negative control: a floated pillar fixture must fail');
const translate=s=>s.replace(/level endon\([^;]+;/g,'').replace(/wait 0\.1;/g,'yield;')
 .replace(/(rotors\[ i \]|rotor|housing) (SetModel|RotateTo|SetScale)\(/g,'$1.$2(')
 .replace(/rotor notify\(/g,'rotor.notify(').replace(/rotor thread spin\(\);/g,'rotor.spin();')
 .replace(/tod_perk_lights::set_glow/g,'glow').replace(/\.size/g,'.length')
 .replace(/tod_power_conduits::init\(\);/g,'conduitInit();').replace(/tod_crown_data::/g,'data.')
 .replace(/orgs\[ i \] \+ \( 0, 0, dz \)/g,'offset(orgs[i],dz)')
 .replace(/rotor.angles = \( ([^\n]+) \);/g,'rotor.angles = [ $1 ];');
function harness(){
 const logs=[],level={tod_fall_sealed:false},spawned=[];
 let draws=0;
 const RandomFloat=max=>{assert.equal(max,360);return ((draws++*137.508)+17.3)%360;};
 const Spawn=(kind,origin)=>{
  const e={origin,fx:0,spins:0,stops:0,SetModel(x){this.model=x;},SetScale(x){this.scale=x;},RotateTo(){this.stops++;},notify(){},spin(){this.spins++;}};
  spawned.push(e);return e;
 };
 const data={alarm_mount_orgs:()=>mounts.map(m=>m.org),alarm_mount_angles:()=>mounts.map(m=>m.angles),alarm_mount_scales:()=>mounts.map(m=>m.scale),alarm_mount_kinds:()=>mounts.map(m=>m.kind)};
 const init=new Function('level','data','Spawn','isdefined','RandomFloat','offset','conduitInit','alarm_log','is_high','off_model','housing_model',
  'return function(){let orgs,angles,scales,kinds,i,housing,dz,rotor,mount_angles;'+translate(body('init'))+'}')(
   level,data,Spawn,x=>x!==undefined,RandomFloat,(v,z)=>[v[0],v[1],v[2]+z],()=>{},m=>logs.push(m),isHigh,k=>offModel(k,isHigh),k=>housingModel(k,isHigh));
 init();const rotors=level.tod_crown_alarm_rotors;
 const args=['level','init','IS_TRUE','isdefined','glow','alarm_log','on_model','is_high','off_model'];
 const values=[level,init,x=>x===true,x=>x!==undefined,(r,x)=>r.fx=x,m=>logs.push(m),onModel,isHigh,k=>offModel(k,isHigh)];
 const start=new Function(...args,'return function*(){let rotors,i,rotor,lights;'+translate(body('start'))+'}')(...values);
 const stop=new Function(...args,'return function(){let rotors,i,rotor;'+translate(body('stop'))+'}')(...values);
 return {level,rotors,logs,start,stop,init,spawned,get draws(){return draws;}};
}
let h=harness();
assert.equal(h.draws,30,'roll once per fixture, including the exterior and pendant');
assert.equal(new Set(h.rotors.map(r=>r.tod_alarm_phase)).size,30);
const initialAngles=h.rotors.map(r=>r.angles.slice());
for(let i=0;i<30;i++){
 const r=h.rotors[i],m=mounts[i];
 assert.deepEqual(r.angles,[m.angles[0],m.angles[1]+r.tod_alarm_phase,m.angles[2]],'randomize only the rotor yaw');
 assert.deepEqual(r.tod_alarm_housing.angles,m.angles,'mounting orientation stays fixed, including the inverted pendant');
 assert.equal(r.model,offModel(m.kind,isHigh));
 assert.equal(r.tod_alarm_housing.model,housingModel(m.kind,isHigh));
 assert.equal(r.origin[2],m.org[2]+(isHigh(m.kind)?48:m.kind==='pendant'?-26:26)*m.scale,'pivot must match the enlarged housing');
 assert(h.logs.some(x=>x.includes('MOUNT id='+i+' ')&&x.includes('phase_degrees='+r.tod_alarm_phase)));
}
h.init();assert.equal(h.draws,30);assert.equal(h.spawned.length,60,'duplicate init must preserve phases and fixtures');
let g=h.start();g.next();assert(h.level.tod_crown_alarm_active);
assert(h.rotors.every(r=>r.model.endsWith('_on')&&r.fx===0));g.next();
assert.equal(h.rotors.filter(r=>r.model==='tod_crown_alarm_rotor_high_on').length,17,'only the sixteen points and apex use the brighter skin');
assert(h.rotors.filter(r=>['pillar','pendant'].includes(r.tod_alarm_kind)).every(r=>r.model==='tod_crown_alarm_rotor_on'),'hall lamps retain their accepted intensity');
assert(h.rotors.every(r=>r.spins===1));assert.equal(h.rotors.filter(r=>r.fx===11).length,13);
assert(h.rotors.filter(r=>isHigh(r.tod_alarm_kind)).every(r=>r.fx===12),'every high fixture casts actual red light');
h.start().next();assert(h.rotors.every(r=>r.spins===1),'duplicate activation must not stack rotation');
assert.equal(h.draws,30);assert.deepEqual(h.rotors.map(r=>r.angles),initialAngles,'activation never rerolls phases');
h.stop();assert(h.rotors.every(r=>r.fx===0&&r.model.endsWith('_off')&&r.stops===1));
h.stop();assert(h.rotors.every(r=>r.stops===1),'duplicate stop must be harmless');
h=harness();g=h.start();g.next();h.level.tod_fall_sealed=true;h.stop();g.next();
assert(h.rotors.every(r=>r.fx===0&&r.spins===0&&r.model.endsWith('_off')),'seal during 0.1s startup must cancel light and rotation');
h.start().next();assert(h.rotors.every(r=>r.model.endsWith('_off')),'sealed crown must never reactivate');
const fx=fs.readFileSync('share/raw/fx/tod/crown_alarm/fx_tod_alarm_sweep.efx','utf8');
function validLightDefinition(text){
 let depth=0;
 for(const c of text){if(c==='{')depth++;else if(c==='}'&&--depth<0)return false;}
 return depth===0&&/dynamicLight2\s*\{\s*New\s*\{[^{}]*\bname light\r?\n[^{}]*\bvolumetricSampleCount 8\s*\};\s*\};/.test(text);
}
assert(validLightDefinition(fx),'native FX light block must be complete with balanced braces');
assert(!validLightDefinition(fx.replace(/name light[\s\S]*?\};/,'name "truncated";')),'negative control: truncated native light must fail');
assert.match(fx,/spawnLooping 1000 0/);assert.match(fx,/lifeSpanMsec 1000 0/);
assert.match(fx,/runRelToEffect/);assert.match(fx,/PRIMARY_TYPE PRIMARY_SPOT/);assert.match(fx,/PRIMARY_NOSHADOWMAP 1/);
for(const graph of fx.matchAll(/colorGraph\s+\d+\s*\{([\s\S]*?)\};/g))
 for(const row of graph[1].matchAll(/^\s*[\d.]+ ([\d.]+) ([\d.]+) ([\d.]+)$/gm))assert.deepEqual(row.slice(1).map(Number),[1,0,0]);
const profile=JSON.parse(fs.readFileSync('tools/crown_alarm/light_profile.json','utf8'));
const highFx=fs.readFileSync('share/raw/fx/tod/crown_alarm/fx_tod_alarm_high.efx','utf8');
assert(validLightDefinition(highFx));
assert.match(highFx,/PRIMARY_TYPE PRIMARY_OMNI/);
assert.match(highFx,/PRIMARY_NOSHADOWMAP 1/);
assert.match(highFx,/spawnLooping 1000 0/);assert.match(highFx,/lifeSpanMsec 1000 0/);
assert.match(highFx,new RegExp('lightIntensityGraph '+profile.high_intensity));
assert.match(highFx,new RegExp('lightRadiusGraph '+profile.high_radius));
assert(profile.high_bounds>=profile.high_radius);
assert.match(highFx,new RegExp('spawnRange 0 '+profile.high_spawn_range));
assert.equal((highFx.match(/\bdynamicLight2\b/g)||[]).length,1);
const csc=fs.readFileSync('scripts/zm/zm_tod2_cybercity/_tod_perk_lights.csc','utf8');
assert(csc.includes('level._effect[ "tod_glow_12" ] = "tod/crown_alarm/fx_tod_alarm_high"'));
assert(csc.includes('#precache( "client_fx", "tod/crown_alarm/fx_tod_alarm_high" )'));
const scalar=name=>Number(fx.match(new RegExp('\\b'+name+' ([\\d.]+)'))[1]);
assert.equal(scalar('lightIntensityGraph'),profile.intensity);
assert.equal(scalar('lightRadiusGraph'),profile.radius);
assert.equal(scalar('lightFovGraph'),profile.fov_degrees);
assert(scalar('spawnFrustumCullRadius')>=profile.radius+Math.hypot(9,2),'frustum must cover the light, not just the visible bulb');
assert.equal((fx.match(/\bdynamicLight2\b/g)||[]).length,1,'no extra lights hidden in the effect');
const bound=Number(fx.match(/efBoundingBoxMax ([\d.]+)/)[1]);
assert(bound>=profile.radius+Math.hypot(9,2),'effect bounds must cover every rotating direction');
assert.match(code,new RegExp('profile='+profile.version+' reach='+profile.radius+' intensity='+profile.intensity+' lamp='+profile.lamp_emission));
assert.match(code,new RegExp('high_lamp='+profile.lamp_emission*profile.high_lamp_multiplier));
assert(fs.readFileSync('zone_source/tod_crown_alarm.zpkg','utf8').includes('xmodel,tod_crown_alarm_rotor_high_on'));
// Horizontal cone reach, evaluated against actual mounting and floor geometry.
// This proves potential coverage, not native attenuation/occlusion or brightness.
const floor=solids.find(s=>s.label==='crown hall floor').hi[2];
function floorIntersections(radius,fov){
 return mounts.filter(m=>['pillar','pendant'].includes(m.kind)).map(m=>{
  const sign=m.kind==='pendant'?-1:1;
  const height=m.org[2]+sign*(26*m.scale+2)-floor;
  const nearest=height/Math.sin(fov*Math.PI/360);
  return {kind:m.kind,height,nearest,reachable:nearest<radius};
 });
}
assert(floorIntersections(profile.radius,profile.fov_degrees).every(x=>x.reachable),'every hall cone must be capable of reaching the floor');
assert(floorIntersections(360,62).every(x=>!x.reachable),'negative control: old short cones cannot reach the floor');
console.log('PASS: 17 enlarged high fixtures + red spill / 13 unchanged hall fixtures; mount support and pivots; random phases; idempotent activation; seal cancellation and shutdown; light bounds/range and client precache.');
