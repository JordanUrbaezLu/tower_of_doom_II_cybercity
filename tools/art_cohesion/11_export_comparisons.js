// Render the HTML comparison layout to standalone images in an owned headless
// Chrome session. Uses only Node built-ins and the local DevTools connection.
const fs=require('fs'),path=require('path'),assert=require('assert');
const {pathToFileURL}=require('url');
const root=path.resolve(__dirname,'../..'),art=path.join(root,'art/cybercity_materials');
const endpoint='http://127.0.0.1:9339';
async function main(){
  const page=await (await fetch(endpoint+'/json/new?'+encodeURIComponent(pathToFileURL(path.join(root,'docs/art_cohesion/review.html')).href),{method:'PUT'})).json();
  const ws=new WebSocket(page.webSocketDebuggerUrl);await new Promise((ok,no)=>{ws.onopen=ok;ws.onerror=no;});
  let id=0;const pending=new Map();
  ws.onmessage=e=>{const m=JSON.parse(e.data);if(m.id&&pending.has(m.id)){const [ok,no]=pending.get(m.id);pending.delete(m.id);m.error?no(Error(JSON.stringify(m.error))):ok(m.result);}};
  const call=(method,params={})=>new Promise((ok,no)=>{const key=++id;pending.set(key,[ok,no]);ws.send(JSON.stringify({id:key,method,params}));});
  const evaluate=async expression=>{const r=await call('Runtime.evaluate',{expression,returnByValue:true,awaitPromise:true});assert(!r.exceptionDetails,JSON.stringify(r.exceptionDetails));return r.result.value;};
  await call('Page.enable');await call('Runtime.enable');
  await call('Emulation.setDeviceMetricsOverride',{width:1800,height:1400,deviceScaleFactor:1,mobile:false});
  await evaluate("Promise.all([...document.images].map(i=>i.decode())).then(()=>true)");
  const results=[];
  for(const view of ['interior','from_tower','exterior','underside']){
    await evaluate(`document.querySelector('button[data-view="${view}"]').click();true`);
    await evaluate("Promise.all(['before','after'].map(s=>document.querySelector('#'+s+'-image').decode())).then(()=>true)");
    const state=await evaluate(`(()=>{const pair=document.querySelector('#comparison-pair'),r=pair.getBoundingClientRect();return {selected:[...document.querySelectorAll('button[aria-pressed="true"]')].map(b=>b.dataset.view),images:['before','after'].map(s=>{const i=document.querySelector('#'+s+'-image');return {src:i.src,width:i.naturalWidth,height:i.naturalHeight}}),clip:{x:r.x+scrollX,y:r.y+scrollY,width:r.width,height:r.height,scale:1}}})()`);
    assert.deepStrictEqual(state.selected,[view]);
    assert(state.images[0].src.endsWith('crown_'+view+'_before.png'));
    assert(state.images[1].src.endsWith('crown_'+view+'.png'));
    assert(state.images[0].width>0&&state.images[0].width===state.images[1].width&&state.images[0].height===state.images[1].height);
    const shot=await call('Page.captureScreenshot',{format:'png',captureBeyondViewport:true,clip:state.clip});
    const name='crown_'+view+'_side_by_side.png';fs.writeFileSync(path.join(art,name),Buffer.from(shot.data,'base64'));
    results.push({view,output:name,images:state.images,matched_dimensions:true,buttons_pass:true});
  }
  await evaluate('document.querySelector(\'button[data-view="interior"]\').click();true');
  await evaluate("Promise.all([...document.images].map(i=>i.decode())).then(()=>true)");
  const desktop=await call('Page.captureScreenshot',{format:'png'});
  fs.writeFileSync(path.join(root,'tmp/art_cohesion/side_by_side_browser.png'),Buffer.from(desktop.data,'base64'));
  fs.writeFileSync(path.join(art,'comparison_ui.json'),JSON.stringify({views:results},null,2)+'\n');
  console.log('COMPARISON_EXPORT_PASS: four matched image pairs; all view buttons work');
  await call('Browser.close');
}
main().catch(e=>{console.error(e);process.exitCode=1;});
