'use strict';
// BO6 native source: tmp/wunderfizz/assets/engine_kit/manifest.json.
// Exact exported pivot/scale retained. Bounds are union of all powered/unpowered
// LODs; collision is the original box plus sloped upper prism, clip_slick.
const HAVEN=require('./haven_layout');
const ASSET={model:'t10_zm_machine_wunderfizz_fxanim',on:'t10_zm_machine_wunderfizz_fxanim_on',sourceSha256:'994390e2f4f76763e0a17a38d7739b574460c2262d688208d97dcee5e5ebff5c',
  mins:[-1.372424,-27.691320,-0.001485],maxs:[51.240486,27.691189,97.765066],frontYaw:0,scale:1,
  triggerOffset:83.240486,triggerRadius:32,triggerLift:53.877693};
const C={core:256,pathOuter:416,depth:120,span:160,slab:16,rail:20,railHeight:39,railCap:168,lapRise:384,flightRise:192,floors:50};
const round=n=>Math.round(n*1000)/1000,rad=d=>d*Math.PI/180;
const rotated=(p,org,yaw)=>{const c=Math.cos(rad(yaw)),s=Math.sin(rad(yaw));return [round(org[0]+p[0]*c-p[1]*s),round(org[1]+p[0]*s+p[1]*c),round(org[2]+p[2])];};
function body(n){return [[ASSET.mins[0],ASSET.mins[1],0],[ASSET.maxs[0],ASSET.mins[1],0],[ASSET.maxs[0],ASSET.maxs[1],0],[ASSET.mins[0],ASSET.maxs[1],0]].map(p=>rotated(p,n.org,n.yaw));}
function nodes(){
 const a=[];
 for(let floor=1;floor<=C.floors;floor++){
  const z=(floor-1)*C.lapRise+C.flightRise,haven=[10,20,30,40].includes(floor),s=floor%2?1:-1;
  const org=haven?[...HAVEN.FURN.wunderfizz.org,z]:[s*336,round(s*(C.pathOuter+C.depth-16+ASSET.mins[0])),z];
  const yaw=haven?HAVEN.FURN.wunderfizz.yaw:(s===1?270:90),f=[round(Math.cos(rad(yaw))),round(Math.sin(rad(yaw))),0];
  const trig=rotated([ASSET.triggerOffset,0,ASSET.triggerLift],org,yaw);
  const n={id:floor,floor,kind:haven?'haven':'alcove',org,yaw,front:f,trig,r:ASSET.triggerRadius};
  if(!haven)n.alcove={x1:s>0?256:-416,x2:s>0?416:-256,y1:s>0?C.pathOuter:-C.pathOuter-C.depth,y2:s>0?C.pathOuter+C.depth:-C.pathOuter,z};
  n.body=body(n);a.push(n);
 }return a;
}
function geometry(api,n){
 const tag='lap'+n.floor+' wunderfizz';
 if(n.alcove){
  const a=n.alcove,{x1,x2,y1,y2,z}=a;
  api.deck(tag+' alcove floor',x1,x2,y1,y2,z-C.slab,z,n.floor);
  const rail=(name,xx1,xx2,yy1,yy2)=>api.rail(tag+' alcove '+name,xx1,xx2,yy1,yy2,z,n.floor);
  rail('east rail',x2,x2+C.rail,y1,y2);rail('west rail',x1-C.rail,x1,y1,y2);
  if(n.floor%2)rail('outer rail',x1-C.rail,x2+C.rail,y2,y2+C.rail);else rail('outer rail',x1-C.rail,x2+C.rail,y1-C.rail,y1);
  api.seed(tag+' alcove',n.trig[0],n.trig[1],z+2);
 }
 // Original lower rectangular collision hull, native scale and rear pivot.
 const lower=[[1.5,-22.5,0],[39.5,-22.5,0],[39.5,22,0],[1.5,22,0],[1.5,-22.5,64],[39.5,-22.5,64],[39.5,22,64],[1.5,22,64]];
 const lowerFaces=[[0,3,2,1],[4,5,6,7],[0,1,5,4],[1,2,6,5],[2,3,7,6],[3,0,4,7]];
 // Upper hull decreases from original rear z101.472222 to front z64.
 const upper=[[1.5,-22.5,64],[39.5,-22.5,64],[39.5,22,64],[1.5,22,64],[1.5,-22.5,101.472222],[1.5,22,101.472222]];
 const upperFaces=[[0,3,2,1],[0,1,4],[1,2,5,4],[2,3,5],[3,0,4,5]];
 api.collision(tag+' lower body',lower.map(p=>rotated(p,n.org,n.yaw)),lowerFaces,'clip_slick');
 api.collision(tag+' upper body',upper.map(p=>rotated(p,n.org,n.yaw)),upperFaces,'clip_slick');
}
function dataGsc(a){const v=p=>'( '+p.map(round).join(', ')+' )';let t=['// GENERATED from tools/wunderfizz_layout.js; native BO6 scale/pivot.','#namespace tod_wunderfizz_data;','','function nodes()','{','    a = [];'];for(const n of a)t.push('    n = SpawnStruct();','    n.id = '+n.id+';','    n.floor = '+n.floor+';','    n.org = '+v(n.org)+';','    n.yaw = '+n.yaw+';','    n.trig = '+v(n.trig)+';','    n.r = '+n.r+';','    n.front = '+v(n.front)+';','    a[ a.size ] = n;');t.push('    return a;','}','');return t.join('\n');}
module.exports={ASSET,C,nodes,geometry,dataGsc,body};
