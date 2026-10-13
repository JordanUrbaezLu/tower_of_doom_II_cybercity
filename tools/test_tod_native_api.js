// Check the actual engine calls against same-VM call sites in the installed
// BO3 stock scripts. Behavioral mocks alone cannot prove an API exists.
'use strict';
const fs = require('fs'), path = require('path'), assert = require('assert/strict');
const root = path.resolve(__dirname, '..');
const stock = 'C:/BO3Tools/TOD2Cybercity/share/raw/scripts';
const apiDocs = 'C:/Program Files (x86)/Steam/steamapps/common/Call of Duty Black Ops III 455130/docs_modtools/bo3_scriptapifunctions.htm';
const targets = walk(path.join(root,'scripts')).map(f=>path.relative(root,f).replaceAll('\\','/'));
const syntax = new Set(['if', 'for', 'foreach', 'while', 'switch', 'return', 'wait', 'waittill', 'endon', 'notify', 'waittillmatch', 'array']);
const macros = new Set(['register_system', 'is_true', 'default']);
function strip(text) {
  return text.replace(/"(?:\\.|[^"\\])*"|\/\/[^\n]*|\/\*[\s\S]*?\*\//g,
    s => s[0] === '"' ? '"' + s.slice(1,-1).replace(/[^\n]/g,' ') + '"' : s.replace(/[^\n]/g,' '));
}
function calls(text, context=text) {
  const src = strip(text), declarations=strip(context), defs = new Set([...declarations.matchAll(/function\s+(?:autoexec\s+|private\s+)*([\w]+)\s*\(/gi)].map(m => m[1].toLowerCase()));
  const defines=new Set([...declarations.matchAll(/^\s*#define\s+(\w+)/gm)].map(m=>m[1].toLowerCase()));
  const result=[];
  for (const m of src.matchAll(/(?<![\w:.&#])([a-z_]\w*)\s*\(/gi)) {
    const name=m[1].toLowerCase();
    if (syntax.has(name) || macros.has(name) || defines.has(name) || defs.has(name)) continue;
    let depth=0, count=0, token=false;
    for (let i=m.index+m[0].length; i<src.length; i++) {
      const c=src[i];
      if (c===')' && depth===0) break;
      if (c==='(' || c==='[' || c==='{') depth++;
      if (c===')' || c===']' || c==='}') depth--;
      if (c===',' && depth===0) count++;
      if (!/\s/.test(c)) token=true;
    }
    result.push({name, args:token?count+1:0, line:src.slice(0,m.index).split('\n').length});
  }
  return result;
}
function includes(file, seen=new Set()) {
  if(seen.has(file)) return '';
  seen.add(file);
  const text=fs.readFileSync(file,'utf8');
  return text+'\n'+[...strip(text).matchAll(/#insert\s+([^;]+);/g)].map(m=>{
    const rel=m[1].trim().replaceAll('\\','/');
    const local=path.join(root,rel), shared=path.join(stock,'..',rel);
    const found=fs.existsSync(local)?local:shared;
    assert(fs.existsSync(found),`Missing insert ${rel} in ${file}`);
    return includes(found,seen);
  }).join('\n');
}
function walk(dir) {
  return fs.readdirSync(dir,{withFileTypes:true}).flatMap(e=>{
    const p=path.join(dir,e.name);
    return e.isDirectory()?walk(p):/\.[gc]sc$/i.test(e.name)?[p]:[];
  });
}
const evidence=new Map();
for (const file of walk(stock)) {
  const side=path.extname(file).slice(1);
  for (const c of calls(fs.readFileSync(file,'utf8'))) {
    const key=`${side}:${c.name}/${c.args}`;
    if (!evidence.has(key)) evidence.set(key,{file:path.relative(stock,file).replaceAll('\\','/'),line:c.line});
  }
}
// The official SDK also documents valid optional-argument forms that stock
// scripts need not exercise (for example client SetDrawName(text)).
const documented=new Map();
for (const [index,line] of fs.readFileSync(apiDocs,'utf8').split('\n').entries()) {
  const name=line.match(/<H1>.*?\b(\w+)\(<I>|<H1>.*?\b(\w+)\(\)/i);
  const vm=line.match(/CLIENT\/SERVER:\s*<\/B>([^<]+)/i);
  if (!name || !vm) continue;
  const params=line.split('</UL>')[0];
  const min=(params.match(/\[MANDATORY\]/g)||[]).length;
  const max=min+(params.match(/\[OPTIONAL\]/g)||[]).length;
  for (const side of ['gsc','csc']) {
    if (!/both/i.test(vm[1]) && !vm[1].toLowerCase().includes(side==='gsc'?'server':'client')) continue;
    for (let n=min;n<=max;n++) documented.set(`${side}:${(name[1]||name[2]).toLowerCase()}/${n}`,
      {file:apiDocs,line:index+1,kind:'official API documentation'});
  }
}
const dlc=JSON.parse(fs.readFileSync(path.join(root,'docs/archer_equipment_evidence/dlc_native_api.json'),'utf8'));
for(const c of dlc.calls) evidence.set(`${c.vm}:${c.name}/${c.args}`,
  {file:dlc.source,line:c.line,kind:'recovered stock DLC source',sha256:dlc.recovered_script_sha256});
// Regression controls for the boot failures and common parser false alarms.
assert.deepEqual(calls('PlaySoundAtPosition(0, "a,b", (1,2,3));').map(c=>[c.name,c.args]),[['playsoundatposition',3]]);
assert.deepEqual(calls('/* StopFXOnTag(a,b,c); */ self PlaySound(0, "//not a comment");').map(c=>[c.name,c.args]),[['playsound',2]]);
assert.equal(calls('#define POSITION (1,2,3)\nfunction f(a) { return (a); } f(1); array(1,2,3);').length,0);
assert.equal(calls('included();','function included() {}').length,0);
assert(documented.has('csc:setdrawname/1'),'SDK optional argument parsing');
assert(documented.has('csc:distance2d/2'),'SDK Both VM parsing');
assert(!evidence.has('csc:playsoundatposition/3')&&!documented.has('csc:playsoundatposition/3'),'client sound regression');
assert(!evidence.has('gsc:stopfxontag/3')&&!documented.has('gsc:stopfxontag/3'),'server FX regression');
assert(!evidence.has('gsc:setclientthirdperson/3')&&!documented.has('gsc:setclientthirdperson/3'),'camera argument regression');
const report=[], failures=[], checked=new Set();
for (const target of targets) {
  const source=target, side=path.extname(target).slice(1);
  const file=path.join(root,source);
  const parts=new Set(), context=includes(file,parts);
  for(const part of parts) {
    const rel=path.relative(root,part).replaceAll('\\','/');
    if(rel.startsWith('../') || checked.has(`${side}:${rel}`)) continue;
    checked.add(`${side}:${rel}`);
    for (const c of calls(fs.readFileSync(part,'utf8'),context)) {
      const key=`${side}:${c.name}/${c.args}`, reference=evidence.get(key)||documented.get(key);
      if (!reference) failures.push(`${rel}:${c.line} ${key} has no same-VM stock or SDK evidence`);
      else report.push({source:rel,vm:side,...c,reference});
    }
  }
}
// Previous boot failures must stay rejected even if a future custom stock
// source accidentally adds these names to the evidence corpus.
for (const target of targets.filter(n=>n.endsWith('.gsc'))) {
  const text=strip(fs.readFileSync(path.join(root,target),'utf8'));
  if (/\b(?:loadfx|stopfxontag)\s*\(/i.test(text)) failures.push(`${target}: unsupported server FX API`);
}
for (const target of targets.filter(n=>n.endsWith('.csc'))) {
  const text=strip(fs.readFileSync(path.join(root,target),'utf8'));
  if (/\bplaysoundatposition\s*\(/i.test(text)) failures.push(`${target}: unsupported client positional-sound API; use an entity PlaySound`);
}
assert.deepEqual(failures,[],failures.join('\n'));
fs.writeFileSync(path.join(root,'docs/archer_equipment_evidence/native_api.json'),JSON.stringify({
  stock_root:stock,api_docs:apiDocs,target_files:targets,checked_sources:[...checked],call_sites:report,scope:'Same VM and argument count observed in installed reference scripts, recovered DLC source or documented in the SDK; does not prove runtime behavior.',native_playtest:false
},null,2)+'\n');
console.log(`TOD NATIVE API: ${report.length} call sites across ${targets.length} scripts have same-VM stock/SDK evidence; unsupported server FX and client sound calls rejected.`);
