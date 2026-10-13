'use strict';
// Authored, fixed layout. No RNG at generation time or runtime. Descending order.
const DROP_LAPS = [48,47,45,43,42,39,37,36,34,32,29,28,26,24,23,19,18,16,14,13,9,7,6,3];
const drops = new Set(DROP_LAPS);
function placement(lap) {
  const s=lap%2?1:-1,b=(lap-1)*384;
  return {lap,s,b,flag:`enter_lap${lap}`,upper:[s*336,s*288,b+192],lower:[s*336,s*237,b+2],
    lo:[s>0?256:-416,-256,b+2],hi:[s>0?416:-256,256,b+82],yaw:s>0?270:90};
}
function reshape(world,boxes,seeds,addBox,stepMat,paraMat,railH=56) {
  const removed=label=>{const m=label.match(/^lap(\d+) ([EW]) (step |stair ramp|para )/);return m&&drops.has(+m[1]);};
  for(const arr of [world,boxes,seeds]) for(let i=arr.length-1;i>=0;i--)if(removed(arr[i].label))arr.splice(i,1);
  for(const lap of DROP_LAPS) {
    const {s,b}=placement(lap),prefix=`lap${lap} broken`;
    const box=(name,x1,x2,y1,y2,z1,z2,mat)=>s>0?addBox(`${prefix} ${name}`,x1,x2,y1,y2,z1,z2,mat):addBox(`${prefix} ${name}`,-x2,-x1,-y2,-y1,z1,z2,mat);
    // Flat catch floor joins the preceding lap at a 2u step. Upper landing is
    // 192u: the missing stair is a 190u drop, matching The Giant's traversal.
    box('catch deck',256,416,-256,256,b-14,b+2,stepMat(lap-1));
    box('outer rail',416,436,-256,256,b+2,b+2+railH,paraMat(lap-1));   // railH = the generator's RAIL_VIS_H (2026-09-29); the lap's rail cap now starts at the floor
    // Close the under-landing pocket visibly; no extra stair or mantle shelf.
    box('landing fascia',256,416,256,276,b+2,b+176,paraMat(lap-1));
    // Broken gate uprights sit OUTSIDE the route, with uneven snapped heights.
    box('frame outer stump',436,456,240,264,b+160,b+238,paraMat(lap-1));
    box('frame core scar',248,256,240,264,b+168,b+216,paraMat(lap-1));
    // Two torn nose plates under the ledge; their tops never form footholds.
    box('nose fragment a',256,304,246,256,b+165,b+190,paraMat(lap-1));
    box('nose fragment b',366,416,248,256,b+154,b+190,paraMat(lap-1));
    seeds.push({label:`lap${lap} broken catch`,org:[s*336,0,b+4]});
  }
}
module.exports={DROP_LAPS,drops,placement,reshape};
