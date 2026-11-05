const { chromium } = require('playwright'); const fs=require('fs');
const OUT='/home/user/cames-lp/sofa-simulation/renders';
const names={A:'A_manner4_canvasBR',B:'B_manner4_europeanGrey_PLT112',C:'C_gracieroII_modeGrey_PLT113',D:'D_gracieroII_europeanGrey_PLT112'};
(async()=>{
  const browser=await chromium.launch({args:['--use-gl=swiftshader','--enable-webgl','--ignore-gpu-blocklist','--enable-unsafe-swiftshader']});
  const page=await browser.newPage({viewport:{width:4000,height:2250},deviceScaleFactor:1});
  page.on('pageerror',e=>console.log('[pageerror]',e.message));
  async function run(url,label,tasks){
    await page.goto(url,{waitUntil:'load'}); await page.waitForFunction(()=>window.__ready===true,{timeout:180000}); await page.waitForTimeout(1500);
    for(const [id,file] of tasks){
      const data=await page.evaluate(async(id)=>{const cv=await window.__sim.composite(id); return cv.toDataURL('image/png');},id);
      fs.writeFileSync(file,Buffer.from(data.split(',')[1],'base64')); console.log('saved',file);
    }
  }
  // labeled
  await run('http://127.0.0.1:8765/index.html?ui=0','labeled',Object.entries(names).map(([k,n])=>[k,`${OUT}/sofa_${n}_labeled.png`]));
  // clean (no overlay)
  await run('http://127.0.0.1:8765/index.html?ui=0&foot=0&dims=0','clean',Object.entries(names).map(([k,n])=>[k,`${OUT}/sofa_${n}.png`]));
  // 2x2 grid labeled
  await page.goto('http://127.0.0.1:8765/index.html?ui=0',{waitUntil:'load'}); await page.waitForFunction(()=>window.__ready===true,{timeout:180000}); await page.waitForTimeout(1000);
  const grid=await page.evaluate(async()=>{const W=4000,H=2250; const cv=document.createElement('canvas'); cv.width=W; cv.height=H; const g=cv.getContext('2d'); g.fillStyle='#111'; g.fillRect(0,0,W,H);
    const ids=['A','B','C','D']; for(let i=0;i<4;i++){const c=await window.__sim.composite(ids[i]); const x=(i%2)*W/2, y=Math.floor(i/2)*H/2; g.drawImage(c,x+4,y+4,W/2-8,H/2-8);}
    return cv.toDataURL('image/png');});
  fs.writeFileSync(`${OUT}/comparison_2x2_labeled.png`,Buffer.from(grid.split(',')[1],'base64')); console.log('saved grid');
  // camera check overlay (room lines) at 2000px
  await page.setViewportSize({width:2000,height:1125});
  await page.goto('http://127.0.0.1:8765/index.html?ui=0&room=1&variant=A',{waitUntil:'load'}); await page.waitForFunction(()=>window.__ready===true,{timeout:180000}); await page.waitForTimeout(1500);
  await page.evaluate(()=>{window.__sim.state.alpha=0.35; window.__sim.update();}); await page.waitForTimeout(2500);
  await page.screenshot({path:`${OUT}/camera_calibration_check.png`}); console.log('saved check');
  // plans svg -> png
  for(const k of ['manner','graciero']){ const svg=fs.readFileSync(`/home/user/cames-lp/sofa-simulation/plans/plan_${k}.svg`,'utf8'); const w=+svg.match(/width="(\d+)"/)[1], h=+svg.match(/height="(\d+)"/)[1];
    await page.setViewportSize({width:w,height:h}); await page.goto(`http://127.0.0.1:8765/plans/plan_${k}.svg`); await page.waitForTimeout(500); await page.screenshot({path:`${OUT}/plan_topview_${k}.png`}); console.log('saved plan',k); }
  await browser.close();
})().catch(e=>{console.error(e);process.exit(1);});
