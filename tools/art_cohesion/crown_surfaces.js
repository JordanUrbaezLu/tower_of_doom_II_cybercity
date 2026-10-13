'use strict';
// Called while generating the map, before the whole-map blackout remap.
const C=require('../convex_brush'),kit=require('./crown_materials.json');
const legacy=require('../tod_black_materials.json');
function onIsland(h,mirror=1) {
  const y1=mirror===1?h.lo[1]:-h.hi[1];
  return y1>=5000&&h.hi[2]>=14000&&h.hi[0]<5000&&h.lo[0]>-5000;
}
function apply(label,text,mirror=1) {
  let changed=0;
  // Leaf brush blocks. GUID strings contain braces too; they are not nesting.
  text=text.replace(/^[ \t]*\{[ \t]*\r?\n(?:(?!^[ \t]*[{}][ \t]*\r?$)[\s\S])*?^[ \t]*\}/gm,block=>{
    if(!block.includes('lightmap_gray'))return block;
    const ps=C.readPlanes(block);if(!ps.length)return block;
    if(!ps.some(p=>/^(mwiii_vertigo_retro_synth_|tod_dark_|tod_door_|tod_black_|tod_cc_)/.test(p.mat)))return block;
    const h=C.hull(ps);if(!onIsland(h,mirror)&&!/^crown (girandole|pendilia)/.test(label))return block;
    return block.replace(/\) (\S+) ([-\d.]+) ([-\d.]+) (?=[-\d.]+ [-\d.]+ [-\d.]+ [-\d.]+ lightmap_gray)/g,(face,name)=>{
      if(/^(clip|caulk|nodraw|sky)/.test(name))return face;
      let role=name.startsWith('tod_cc_')?name.slice(7):null;
      if(name.startsWith('tod_door_'))role='door';
      if(!role){
        const suffix=name.startsWith('mwiii_vertigo_retro_synth_')?name.slice(26):name.startsWith('tod_black_')?name.slice(10):legacy.hall_to_black[name];
        role=kit.suffixes[suffix];if(!role)throw Error(`CROWN ART: unmapped ${name} on ${label}`);
      }
      // Walkable surfaces get tread, rather than wall/ornament armor. All
      // aliases preserve the original material's deck/block classification.
      if(/^(causeway (launch deck|overlook|F approach|F gate flare|hallway (junction|east|west|south|power room|teleporter room)$)|uplink dais|crown hall sanctuary tier)/.test(label)&&!/(under-glow|rail|guard)/.test(label))role='gold_deck';
      if(/^extraction pad$/.test(label))role='exfil';
      if(/crown hall floor|crown hall shop bay floor/.test(label))role='floor';
      if(name.startsWith('tod_door_')||/fall gate slab|door enter_roof/.test(label))role='door';
      const def=kit.materials[role];if(!def)throw Error(`CROWN ART: unknown ${role}`);
      changed++;return `) tod_cc_${role} ${def.size} ${def.size} `;
    });
  });
  return {text,changed};
}
module.exports={apply,onIsland};
