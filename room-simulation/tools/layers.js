const { chromium } = require('playwright'); const fs=require('fs');
const S='/tmp/claude-0/-home-user-cames-lp/d255b67e-5213-527c-9cc9-aa92091d8f96/scratchpad/work3';
(async()=>{const b=await chromium.launch({args:['--use-gl=swiftshader','--enable-unsafe-swiftshader']});const p=await b.newPage({viewport:{width:1920,height:1080}});
p.on('pageerror',e=>console.log('[pageerror]',e.message));
const cfg=JSON.parse(process.argv[2]||'{}');
for(const pat of ['A','B']){
  await p.goto(`http://127.0.0.1:8766/index.html?ui=0&pattern=${pat}`,{waitUntil:'load'});await p.waitForFunction(()=>window.__ready===true,{timeout:60000});await p.waitForTimeout(1000);
  for(const cam of ['photo','photo1']){
    const L=await p.evaluate(([cam,cfg])=>{window.__sim.state.labels=false;window.__sim.state.pulled=false;window.__sim.update();return window.__sim.shotLayers(cam,cfg);},[cam,cfg]);
    fs.writeFileSync(`${S}/L_${pat}_${cam}_room.png`,Buffer.from(L.room.split(',')[1],'base64')); fs.writeFileSync(`${S}/L_${pat}_${cam}_furn.png`,Buffer.from(L.furn.split(',')[1],'base64')); console.log('layers',pat,cam);
  }}
await b.close();})();
