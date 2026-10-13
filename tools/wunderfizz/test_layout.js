#!/usr/bin/env node
'use strict';
const fs=require('fs'),path=require('path'),crypto=require('crypto');
const opt=name=>{const i=process.argv.indexOf(name);if(i<0)return null;if(!process.argv[i+1])throw Error(name+' requires a path');return path.resolve(process.argv[i+1]);};
// Shipping defaults use this repo. Explicit stage/generated paths permit isolated
// candidate review without landing a partial map or changing any asset receipt.
const oldCandidate=opt('--candidate'),ROOT=opt('--root')||oldCandidate||path.resolve(__dirname,'../..');
const STAGE=opt('--layout-stage')||path.join(ROOT,oldCandidate?'tmp/wunderfizz/layout/staged_sources/tools':'tools');
const GEN=opt('--generated')||(oldCandidate?path.join(ROOT,'tmp/wunderfizz/layout/generated'):ROOT);
const {gscLoad}=require(path.join(ROOT,'tools/sky_ships/gsc_eval'));
const layout=require(path.join(STAGE,'wunderfizz_layout')),haven=require(path.join(ROOT,'tools/haven_layout'));
const nav=require('./native_navcheck'),nodes=layout.nodes(),read=p=>fs.readFileSync(p,'utf8');
const map=read(path.join(GEN,'map_source/zm/zm_tod2_cybercity.map'));
const source=read(path.join(STAGE,'gen_tower_map.js')),data=read(path.join(GEN,'scripts/zm/zm_tod2_cybercity/_tod_wunderfizz_data.gsc'));
const manifestFile=path.join(ROOT,'art/wunderfizz/asset_manifest.json'),motionFile=path.join(ROOT,'art/wunderfizz/motion_bounds.json');
const BASE_FURN={
 pap:{org:[150.493,-126.299],trig:[138.061,-79.931],yaw:195,r:32,face:105,back:48,half:52,h:112,front:[-.259,.966]},
 station:{org:[335,92],trig:[299,92],yaw:270,r:64,face:180,back:19,half:51,h:131,front:[-1,0]},
 crate:{org:[-184,92],trig:[-128,92],yaw:270,r:72,face:0,back:37,half:49,h:30,front:[1,0]}
};
let pass=0,fail=0;function check(ok,s){if(ok){pass++;console.log('ok '+s);}else{fail++;console.error('FAIL '+s);}}
const hash=b=>crypto.createHash('sha256').update(b).digest('hex');
check(!/"targetname" "zm_perk_machine"|"targetname" "zombie_vending"/.test(map),'all nine individual model/purchase structs removed');
check(nodes.length===4&&nodes.map(n=>n.floor).join(',')==='10,20,30,40'&&nodes.every(n=>n.id===n.floor&&n.kind==='haven'&&!n.alcove),'exactly one machine in each existing haven10/20/30/40; no other floor machines');
const placement=nav.placementProblems(nodes,{haven,asset:layout.ASSET});
check(placement.length===0,'all animated bodies and standing probes fit the actual haven hall and spherical dome: '+placement.join('; '));
const g=gscLoad([['tod_wunderfizz_data',data]],{},{}),actual=g.call('tod_wunderfizz_data::nodes',[]);
check(actual.length===4&&actual.every((n,i)=>n.floor===nodes[i].floor&&n.id===nodes[i].id&&n.yaw===nodes[i].yaw&&n.r===nodes[i].r&&[0,1,2].every(a=>n.org[a]===nodes[i].org[a]&&n.trig[a]===nodes[i].trig[a]&&n.front[a]===nodes[i].front[a])),'generated GSC descriptors execute with exact four-haven authoring parity');
check(nodes.every(n=>n.org[0]===haven.FURN.wunderfizz.org[0]&&n.org[1]===haven.FURN.wunderfizz.org[1]&&n.yaw===haven.FURN.wunderfizz.yaw),'four haven counters retain the reviewed original south-west pad and inward facing');
check(!/wunderfizz alcove/.test(map)&&!source.includes('wfAlcove'),'all46 ordinary side alcoves and their landing/rail branches removed');
check(Object.keys(haven.VEND).join(',')==='pap,station,crate,wunderfizz','haven retains PaP/altar/crate and one Wunderfizz pad');
for(const key of ['pap','station','crate'])check(JSON.stringify(BASE_FURN[key])===JSON.stringify(haven.FURN[key]),'existing haven '+key+' anchor preserved');
const sourceNative=JSON.parse(read(manifestFile)),motion=JSON.parse(read(motionFile));
check(layout.ASSET.scale===sourceNative.scale&&layout.ASSET.frontYaw===sourceNative.frontYaw&&layout.ASSET.model===sourceNative.model_names.off&&layout.ASSET.on===sourceNative.model_names.on,'original source model identity/scale/rear pivot/+X facing retained');
check(layout.ASSET.sourceSha256===hash(fs.readFileSync(manifestFile)),'unchanged exact BO6 source receipt pinned');
check(motion.models.length===14&&new Set(motion.models.map(m=>m.file)).size===14&&motion.animation_frames===121&&motion.animation_fps===30,'bounds evidence includes all14 originalLODs and all121 activationframes');
const motionUnion=[0,1,2].map(a=>[Math.min(...motion.models.map(m=>m.bounds[a][0])),Math.max(...motion.models.map(m=>m.bounds[a][1]))]);
const sourceBoundsMatch=asset=>motionUnion.every((b,i)=>Math.abs(asset.mins[i]-b[0])<.000001&&Math.abs(asset.maxs[i]-b[1])<.000001);
check(sourceBoundsMatch(layout.ASSET),'placement fit retains full measured original animated source bounds');
check(!sourceBoundsMatch({...layout.ASSET,maxs:layout.ASSET.maxs.map((v,i)=>v-(i===2?1:0))}),'truncated animated source bounds rejected');
const collision=[];for(const n of nodes)layout.geometry({deck:()=>{},rail:()=>{},seed:()=>{},collision:(label,verts,faces,mat)=>collision.push({label,verts,faces,mat})},n);
check(sourceNative.collision.hulls.length===2&&collision.length===8&&collision.every(c=>c.mat==='clip_slick'),'eight original native collision hulls across the four counters with exact source surface');
check((map.match(/lap\d+ wunderfizz (lower|upper) body/g)||[]).length===8&&[...map.matchAll(/lap(\d+) wunderfizz (lower|upper) body/g)].every(m=>nav.HAVEN_FLOORS.includes(+m[1])),'generated map has only eight hulls on haven10/20/30/40');
check(collision.every((c,i)=>{
 const n=nodes[Math.floor(i/2)],h=sourceNative.collision.hulls[i%2],angle=-n.yaw*Math.PI/180,co=Math.cos(angle),si=Math.sin(angle);
 const local=c.verts.map(v=>{const x=v[0]-n.org[0],y=v[1]-n.org[1];return [x*co-y*si,x*si+y*co,v[2]-n.org[2]];});
 return c.faces.length===h.planes&&local.length===h.corners.length&&local.every(v=>h.corners.some(p=>p.every((a,k)=>Math.abs(a-v[k])<.0015)));
}),'all four collision pairs retain original source corners and plane counts after placement rounding');
check(collision.every((c,i)=>c.verts.every(v=>v.every(Number.isFinite)&&haven.onFloor(v)&&haven.domeZ(Math.hypot(v[0]-haven.C[0],v[1]-haven.C[1]))>=v[2]-nodes[Math.floor(i/2)].org[2]+8)),'original upper/lower hulls remain wholly inside each actual haven dome');
const broken=require(path.join(ROOT,'tools/broken_tower_layout')),routes=require(path.join(ROOT,'tools/broken_tower_contract')).read(map);
check(routes.length===24&&routes.map(r=>r.lap).sort((a,b)=>b-a).join(',')===broken.DROP_LAPS.join(',')&&routes.every(r=>{const p=broken.placement(r.lap);return JSON.stringify(r.from)===JSON.stringify(p.upper)&&JSON.stringify(r.to)===JSON.stringify(p.lower);}), 'all24 directed stock drops retain their exact takeoff/catch anchors independently of machines');
check(broken.DROP_LAPS.every(f=>map.includes('lap'+f+' broken catch deck')&&map.includes('lap'+f+' broken upper trigger')&&map.includes('lap'+f+' broken lower trigger')),'all24 broken catch decks and directed drop triggers remain');
check(/"targetname" "tod_jumppad_launch"/.test(map)&&/"targetname" "tod_jumppad_land"/.test(map),'existing one-way crown jump route markers retained');
check((map.match(/dealer presence floor20_service canonical dealer portrait/g)||[]).length===1,'floor20 Dealer identity panel retained');
check((map.match(/"model" "_prefabs\/ALXS\/alxs_cwpap_prefab.map"/g)||[]).length===1,'exactly one native crown PaP prefab preserved');
const crown=map.match(/\/\/ entity \d+[^\n]*crown pack-a-punch\r?\n(\{[\s\S]*?\n\})/);
check(crown&&crown[1].includes('"origin" "664 8608 19392"')&&crown[1].includes('"angles" "0 0 0"'),'crown PaP route anchor/orientation preserved');
const parentNav=read(path.join(ROOT,'tools/lint_tod_navmesh.js'));
check(parentNav.includes("require('./broken_tower_navcheck')")&&parentNav.includes('for (const b of crown.bad)')&&parentNav.includes('for (const b of transitBad)')&&parentNav.includes('for (const b of arena.bad)')&&parentNav.includes('for (const b of house.bad)'),'native parent retains directed-drop/crown/transit/arena/Dealer route failure gates');
check(['gen_tower_map.js','haven_layout.js','lint_tod_geometry.js'].every(name=>{const p=fs.existsSync(path.join(STAGE,name))?path.join(STAGE,name):path.join(ROOT,'tools',name);return !/(?<!\r)\n/.test(read(p));}), 'tracked generator/haven/geometry sources preserve existing CRLF endings');
console.log('\n'+pass+' passed; '+fail+' failed. Static authoring/data contracts; native build/navmesh and user playtest are separate proofs.');process.exitCode=fail?1:0;
