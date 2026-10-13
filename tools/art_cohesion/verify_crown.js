'use strict';
const fs=require('fs'),path=require('path'),assert=require('assert'),cp=require('child_process');
const root=path.resolve(__dirname,'../..'),art=path.join(root,'art/cybercity_materials');
cp.execFileSync(process.execPath,[path.join(__dirname,'inventory_crown.js')],{stdio:'ignore'});
const before=JSON.parse(fs.readFileSync(path.join(art,'crown_before_refactor.json'))),now=JSON.parse(fs.readFileSync(path.join(art,'crown_inventory.json')));
// The alarm's dummy cube was explicitly replaced with a native physical beacon.
const exceptions=/^crown hall (floor|shop bay floor)|^crown wall W|^crown hall alarm core$/;
const signature=r=>r.faces.map(f=>[...f.n,f.d].map(v=>Math.round(v*1e5)/1e5).join(',')).sort().join('|');
// User 2026-09-27: open the jump-pad overlook. Permit ONLY a 56 -> 12u
// top-face reduction on these five rails; retain every footprint/bottom/side.
// test_jumppad separately proves the full-height invisible player barriers.
const loweredCurbs=new Set(['causeway rail W8','causeway rail S9','causeway rail N10','causeway rail N11','causeway rail E12']);
const approvedSignature=r=>signature(loweredCurbs.has(r.label)?{...r,faces:r.faces.map(f=>f.n[2]===1?{...f,d:f.d-44}:f)}:r);
const expected=new Map(before.rows.filter(r=>!exceptions.test(r.label)).map(r=>[r.label,approvedSignature(r)]));
for(const r of now.rows) {
  assert(r.materials.every(m=>m.startsWith('tod_cc_')),r.label+' still uses '+r.materials.join(','));
  if(!exceptions.test(r.label)){assert.strictEqual(signature(r),expected.get(r.label),r.label+' changed shape');expected.delete(r.label);}
}
assert.strictEqual(expected.size,0,'Missing crown solids: '+[...expected.keys()].join(', '));
for(const prefix of ['causeway launch deck','causeway hallway','crown skirt','crown wall','crown hall','crown girandole','crown finial','crown ermine','crown point'])assert(now.rows.some(r=>r.label.startsWith(prefix)),prefix);
const map=fs.readFileSync(path.join(root,'map_source/zm/zm_tod2_cybercity.map'),'utf8');
const gate=map.split('— door slab tod_fall')[1]?.split('// entity')[0];assert(gate&&gate.includes('tod_cc_door'),'Crown gate must use the new material');
const report={world_brushes:now.brushes,world_faces:now.rows.reduce((s,r)=>s+r.faces.length,0),world_materials:Object.keys(now.materials),old_crown_surface_materials_remaining:0,unchanged_solid_geometry:false,authorized_balcony_curbs:5,other_crown_geometry_unchanged:true,gate_material:'tod_cc_door',coverage:['interior','outer shell','underside','jewels','ornament','approach','balcony','hallway']};
fs.writeFileSync(path.join(art,'crown_validation.json'),JSON.stringify(report,null,2));console.log('CROWN_ART_PASS',JSON.stringify(report));
