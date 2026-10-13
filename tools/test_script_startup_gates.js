// Exercise the actual startup linters with in-memory broken source files.
// No shipping source or deployment is changed by these negative controls.
'use strict';
const fs=require('fs'),path=require('path'),vm=require('vm'),assert=require('assert/strict');
const root=path.resolve(__dirname,'..');
function run(tool,relative,append) {
  const file=path.join(root,relative), output=[];
  const mockFs=Object.create(fs);
  mockFs.readFileSync=(name,...args)=>{
    const data=fs.readFileSync(name,...args);
    return path.resolve(name)===file?data+append:data;
  };
  mockFs.writeFileSync=()=>{}; // Preserve the real passing evidence report.
  const processState={exitCode:0}; let error;
  try {
    vm.runInNewContext(fs.readFileSync(path.join(__dirname,tool),'utf8'),{
      require:name=>name==='fs'?mockFs:require(name),__dirname,
      console:{log:line=>output.push(line)},process:processState
    });
  } catch(e) {error=e;}
  return {failed:!!error||processState.exitCode!==0,text:error?String(error):output.join('\n')};
}
const cases=[
  ['test_tod_native_api.js','scripts/zm/zm_tod2_cybercity/_tod_retriever.gsc','\nStopFXOnTag(a,b,c);','stopfxontag'],
  ['test_tod_native_api.js','scripts/zm/zm_tod2_cybercity/_tod_boss_fx.csc','\nPlaySoundAtPosition(0,"sound",(1,2,3));','playsoundatposition'],
  ['test_tod_native_api.js','scripts/zm/_zm_aetherium_hud.gsc','\nself SetClientThirdPerson(1,120,30);','setclientthirdperson'],
  ['lint_tod_arity.js','scripts/zm/zm_tod2_cybercity/_tod_boss_fx.csc','\nmissing_test_namespace::missing();','missing_test_namespace'],
  ['lint_tod_arity.js','scripts/zm/zm_tod2_cybercity/_tod_boss_fx.csc','\nshot_cb(1,2,3,4,5,6,7,8);','ARITY']
];
for(const [tool,file,append,expected] of cases) {
  const result=run(tool,file,append);
  assert(result.failed&&result.text.includes(expected),`${tool} failed to reject ${expected}: ${result.text}`);
}
console.log(`STARTUP GATE SELFTEST: ${cases.length} injected native/script startup errors correctly rejected; source files unchanged.`);
