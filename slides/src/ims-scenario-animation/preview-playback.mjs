// Exercise the local GenOffice renderer in an isolated, headless desktop session.
import { _electron } from '/home/jjd/genoffice/node_modules/playwright/index.mjs';
import { mkdtemp, writeFile, mkdir } from 'node:fs/promises';
import { join, resolve } from 'node:path';
const profile=await mkdtemp('/tmp/ims-genoffice-play-');
await writeFile(join(profile,'app-settings.json'),JSON.stringify({onboardingSeen:true,analyticsEnabled:false}));
const {ELECTRON_RUN_AS_NODE:unused,...env}=process.env;
let app;
try {
  app=await _electron.launch({
    executablePath:'/home/jjd/genoffice/node_modules/electron/dist/electron',
    args:['--no-sandbox','--disable-gpu','--ozone-platform=headless','/home/jjd/genoffice/apps/shell',
      resolve(process.argv[2]||'slides/src/ims-scenario-animation/IMS_scenario.pptx')],
    env:{...env,GENOFFICE_USER_DATA:profile,GENOFFICE_NO_SPARE_VIEW:'1',GENOFFICE_LANG:'en',ELECTRON_DISABLE_SANDBOX:'1'},
    timeout:25000
  });
  let slides;
  for(let attempt=0;attempt<80;attempt++) {
    for(const page of app.windows()) {
      const href=await page.evaluate(()=>location.href).catch(()=>'');
      if(href.includes('slides')&& !href.includes('shell')) slides=page;
    }
    if(slides) break;
    await new Promise(r=>setTimeout(r,200));
  }
  if(!slides) throw new Error('Slides renderer not found: '+JSON.stringify(await Promise.all(app.windows().map(p=>p.evaluate(()=>location.href).catch(()=>p.url())))));
  await slides.waitForFunction(()=>document.body.innerText.includes('Slide'),{timeout:15000});
  const out=resolve('ims-scenario-animation/playback-previews');await mkdir(out,{recursive:true});
  await slides.screenshot({path:join(out,'editor.png')});
  const animations=await slides.evaluate(async()=>[await window.slidesApi.getAnimations(0),await window.slidesApi.getAnimations(1)]);
  console.log('Loaded native animations:',animations.map(a=>a.length));
  await slides.locator('.status-play-btn').click();
  await slides.locator('.slideshow').waitFor({state:'visible'});
  await slides.waitForTimeout(1000);
  for(let page=0;page<2;page++) {
    const groups=animations[page].filter(a=>a.trigger==='onClick').length;
    await slides.locator('.slideshow').screenshot({path:join(out,`page${page+8}-before.png`)});
    for(let step=0;step<groups;step++) {
      await slides.keyboard.press('ArrowRight');
      if(step===0) {
        await slides.waitForTimeout(1050);
        await slides.locator('.slideshow').screenshot({path:join(out,`page${page+8}-moving.png`)});
        await slides.waitForTimeout(2750);
        await slides.locator('.slideshow').screenshot({path:join(out,`page${page+8}-after-first.png`)});
      } else await slides.waitForTimeout(3800);
    }
    await slides.locator('.slideshow').screenshot({path:join(out,`page${page+8}-complete.png`)});
    console.log(`Played page ${page+8}: ${groups} steps`);
    if(page===0) {await slides.keyboard.press('ArrowRight');await slides.waitForTimeout(1000);}
  }
  console.log('Playback screenshots saved:',out);
} finally {
  if(app) {
    await app.evaluate(({dialog})=>{dialog.showMessageBox=async()=>({response:1,checkboxChecked:false})}).catch(()=>{});
    const timer=setTimeout(()=>app.process().kill('SIGKILL'),5000);
    await app.close().catch(()=>{});clearTimeout(timer);
  }
}
