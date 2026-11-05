// Usage: node shot.js <url> <out.png> <viewportW> <viewportH> [clipToStage]
const { chromium } = require('playwright');
(async()=>{
  const [url,out,W,H]=process.argv.slice(2);
  const browser=await chromium.launch({args:['--use-gl=swiftshader','--enable-webgl','--ignore-gpu-blocklist','--enable-unsafe-swiftshader']});
  const page=await browser.newPage({viewport:{width:+W,height:+H},deviceScaleFactor:1});
  page.on('console',m=>{ if(m.type()==='error'||m.type()==='warning') console.log('[console]',m.type(),m.text().slice(0,300)); });
  page.on('pageerror',e=>console.log('[pageerror]',e.message));
  await page.goto(url,{waitUntil:'load'});
  await page.waitForFunction(()=>window.__ready===true,{timeout:120000});
  await page.waitForTimeout(1500);
  await page.evaluate(()=>window.__sim.render()); await page.waitForTimeout(2500);
  await page.screenshot({path:out});
  await browser.close(); console.log('saved',out);
})().catch(e=>{console.error(e);process.exit(1);});
