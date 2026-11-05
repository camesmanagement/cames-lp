const { chromium } = require('playwright'); const fs=require('fs');
const OUT='/home/user/cames-lp/room-simulation/renders'; const BASE='http://127.0.0.1:8766/index.html';
(async()=>{
  const browser=await chromium.launch({args:['--use-gl=swiftshader','--enable-webgl','--ignore-gpu-blocklist','--enable-unsafe-swiftshader']});
  const page=await browser.newPage({viewport:{width:1920,height:1080},deviceScaleFactor:1});
  page.on('pageerror',e=>console.log('[pageerror]',e.message)); page.on('console',m=>{if(m.type()==='error')console.log('[console]',m.text().slice(0,200));});
  const shots=[['entrance','1_entrance_to_balcony'],['balcony','2_balcony_to_kitchen'],['overview','3_overview'],['photo','4_same_angle_as_photo2'],['photo1','4b_same_angle_as_photo1'],['top','5_top_view']];
  for(const pat of ['A','B']){
    await page.goto(`${BASE}?ui=0&pattern=${pat}`,{waitUntil:'load'}); await page.waitForFunction(()=>window.__ready===true,{timeout:120000}); await page.waitForTimeout(1500);
    for(const [k,name] of shots){ await page.evaluate(k=>{window.__sim.state.labels=(k==='top'); window.__sim.update(); window.__sim.setPreset(k);},k); await page.waitForTimeout(900);
      const data=await page.evaluate(()=>window.__sim.shot()); fs.writeFileSync(`${OUT}/pattern${pat}_${name}.png`,Buffer.from(data.split(',')[1],'base64')); console.log('saved',pat,name); }
    // night version of photo angle
    await page.evaluate(()=>{window.__sim.state.labels=false; window.__sim.state.day=false; document.getElementById('optDay').checked=false; document.getElementById('optDay').dispatchEvent(new Event('change'));}); await page.waitForTimeout(600);
    const dn=await page.evaluate(()=>window.__sim.shot('photo')); fs.writeFileSync(`${OUT}/pattern${pat}_4_same_angle_as_photo2_night.png`,Buffer.from(dn.split(',')[1],'base64'));
    const dn1=await page.evaluate(()=>window.__sim.shot('photo1')); fs.writeFileSync(`${OUT}/pattern${pat}_4b_same_angle_as_photo1_night.png`,Buffer.from(dn1.split(',')[1],'base64'));
    // plan svg -> png
    await page.goto(`${BASE}?ui=0&pattern=${pat}&view=plan`,{waitUntil:'load'}); await page.waitForFunction(()=>window.__ready===true,{timeout:120000}); await page.waitForTimeout(800);
    const svg=await page.evaluate(()=>window.__sim.planSVG()); fs.writeFileSync(`/home/user/cames-lp/room-simulation/plans/plan_pattern${pat}.svg`,svg);
    const el=await page.$('#planHost svg'); await el.screenshot({path:`${OUT}/plan_pattern${pat}.png`}); console.log('saved plan',pat);
  }
  // UI screenshot
  await page.goto(`${BASE}?pattern=A`,{waitUntil:'load'}); await page.waitForFunction(()=>window.__ready===true,{timeout:120000}); await page.waitForTimeout(1500); await page.screenshot({path:`${OUT}/ui_overview.png`});
  await browser.close();
})().catch(e=>{console.error(e);process.exit(1);});
