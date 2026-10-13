'use strict';

// Three fixed sightings on existing opaque walls. Native map and Blender
// review consume these same quads, UVs and material names; no runtime entities.
const fs = require('fs');
const path = require('path');
const VERSION = 'dealer_presence_1';
const PHOTO = 'mtl_tod_dealer_surveillance';
function geometry({CM=1, TOP2=19392, CORE=256, LAP_RISE=384, FLIGHT_RISE=192}={}) {
  const mid20 = 19 * LAP_RISE + FLIGHT_RISE;
  const placements = [
    {id:'crown_junction', centre:[-318*CM,6360*CM,TOP2+88], normal:[CM,0,0], width:96,height:112,
      support:'causeway hallway junction west wall',wall_plane:-320*CM,
      camera:[-90*CM,6400*CM,TOP2+60]},
    {id:'floor20_service', centre:[-192,-CORE-2,mid20+104], normal:[0,-1,0], width:64,height:80,
      support:'core band lap20 SW, beside the SW lounge approach',wall_plane:-CORE,
      camera:[-308,-405,mid20+60]},
    {id:'lower_power_corridor', centre:[1040,-422,64], normal:[0,-1,0], width:64,height:80,
      support:'power hall wall N',wall_plane:-420,
      camera:[912,-502,60]},
  ];
  const quads=[];
  for(const p of placements) {
    const [nx,ny]=p.normal, right=[-ny,nx,0];
    const point=(x,z,depth=0)=>p.centre.map((v,i)=>v+right[i]*x+(i===2?z:0)+p.normal[i]*depth);
    const quad=(part,mat,points,uv)=>quads.push({id:p.id,part,material:mat,verts:points,uv});
    const w=p.width/2,h=p.height/2,b=3;
    const rect=(part,mat,x1,x2,z1,z2,d,photo=false)=>quad(part,mat,
      [point(x1,z1,d),point(x2,z1,d),point(x2,z2,d),point(x1,z2,d)],
      photo?[[0,0],[1,0],[1,1],[0,1]]:[[x1/128,z1/128],[x2/128,z1/128],[x2/128,z2/128],[x1/128,z2/128]]);
    // Thin bevelled graphite surround, square screen, short service footer.
    rect('left bezel','tod_cc_graphite',-w,-w+b,-h,h,0);
    rect('right bezel','tod_cc_graphite',w-b,w,-h,h,0);
    rect('top bezel','tod_cc_graphite',-w+b,w-b,h-b,h,0);
    const imageTop=h-b, imageBottom=imageTop-(p.width-2*b);
    rect('footer','tod_cc_graphite',-w+b,w-b,-h,imageBottom,0);
    rect('canonical dealer portrait',PHOTO,-w+b,w-b,imageBottom,imageTop,-.3,true);
    // Four sloping perimeter faces meet the supporting wall (1.8u maximum proud).
    const rim=[[-w,-h],[w,-h],[w,h],[-w,h]];
    for(let i=0;i<4;i++) {
      const a=rim[i],c=rim[(i+1)%4],out=q=>[q[0]+Math.sign(q[0])*.7,q[1]+Math.sign(q[1])*.7];
      const ao=out(a),co=out(c);
      quad('edge bevel '+i,'tod_cc_graphite',[point(...ao,-1.8),point(...co,-1.8),point(...c),point(...a)],[[0,0],[1,0],[1,.02],[0,.02]]);
    }
    // Small worn-metal captive fasteners and an unlit service index.
    for(const x of [-w+1.5,w-1.5]) for(const z of [-h+1.5,h-1.5])
      rect('fastener','tod_cc_bronze_wall',x-.55,x+.55,z-.55,z+.55,.12);
    rect('service index','tod_cc_bronze_wall',-w+8,-w+18,-h+4,-h+5,.1);
  }
  for(const q of quads) {
    if(q.verts.some(v=>v.some(n=>!Number.isFinite(n))))throw Error('non-finite Dealer geometry');
    const p=placements.find(p=>p.id===q.id);
    for(const v of q.verts) {
      const outward=v.reduce((s,n,i)=>s+(n-p.centre[i])*p.normal[i],0)+2;
      if(outward<.19||outward>2.13)throw Error('Dealer panel leaves its thin wall envelope');
    }
  }
  return {version:VERSION,placements,quads,triangles:quads.length*2,
    collision:false,entities:0,lights:0,runtime_threads:0};
}

function emit({worldBrushes,guid,...config}) {
  const result=geometry(config);
  for(const q of result.quads) {
    // Radiant's 2x2 patch stores [bottom, top] for the viewer's left/right columns.
    const vertex=i=>{const p=q.verts[i],uv=q.uv[i];return `\tv ${p.join(' ')} t ${uv[0]*1024} ${-uv[1]*1024} 0 0`;};
    worldBrushes.push({label:`dealer presence ${q.id} ${q.part}`,text:[
      '{',` guid "${guid()}"`,' mesh',' {',' contents nonColliding;',' toolFlags;',
      `  ${q.material}`,'  lightmap_gray','  2 2 0 8','  (',vertex(0),vertex(3),'  )','  (',vertex(1),vertex(2),'  )',' }','}',
    ].join('\n')});
  }
  return result;
}
module.exports={geometry,emit,VERSION,PHOTO};
if(require.main===module) {
  const file=path.resolve(__dirname,'../../art/dealer_presence/geometry.json');
  fs.mkdirSync(path.dirname(file),{recursive:true});
  fs.writeFileSync(file,JSON.stringify(geometry(),null,2)+'\n');
  console.log(`DEALER_PRESENCE_GEOMETRY ${geometry().triangles} triangles, 3 wall panels, no collision/entities/lights`);
}
