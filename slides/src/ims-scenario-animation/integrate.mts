/** Use GenOffice's own engine to preserve source slides and native timings. */
import { readFile, writeFile } from 'node:fs/promises';
import { createHash } from 'node:crypto';
import { fileURLToPath } from 'node:url';
import { dirname, resolve, join } from 'node:path';
import assert from 'node:assert/strict';
import { openPptx, savePptx, copySlide, pasteSlide, getSlideAnimations } from '/home/jjd/genoffice/packages/pptx-engine/src/index.ts';
import { buildSteps, computeNodeStates } from '/home/jjd/genoffice/apps/slides/src/renderer/animation-play.ts';

const root=dirname(fileURLToPath(import.meta.url));
const source=resolve(root,'../../VoNR_over_IMS_kamailio_intro.pptx');
const out=resolve(root,process.argv[3]||'../../VoNR_over_IMS_kamailio_intro_animated.pptx');
const original=await readFile(source);
const originalHash=createHash('sha256').update(original).digest('hex');
const base=await openPptx(original);
const scenario=await openPptx(await readFile(resolve(root,process.argv[2]||'IMS_scenario.pptx')));
assert.equal(base.deck.slides.length,25);
assert.equal(scenario.deck.slides.length,3);
const expectedClicks=[7,6,3];
const verification=[];
for(let i=0;i<3;i++) {
  const animations=getSlideAnimations(scenario.deck.slides[i]);
  const items=animations.map(a=>({...a,sourceId:String(a.spid)}));
  const steps=buildSteps(items);
  assert.equal(steps.length,expectedClicks[i]);
  assert(steps.every(s=>!s.auto));
  const start=computeNodeStates(steps,0,null,720,1280);
  for(const step of steps) {
    for(const {item} of step.items) {
      if(item.effect==='motionPath') assert.equal(start.get(item.sourceId)?.hidden,true);
    }
  }
  const moving=[];
  for(let k=0;k<steps.length;k++) {
    const step=steps[k];
    const final=computeNodeStates(steps,k+1,null,720,1280);
    for(const {item,startMs,endMs} of step.items) {
      if(item.effect!=='motionPath') continue;
      const mid=computeNodeStates(steps,k,startMs+(endMs-startMs)*0.37,720,1280).get(item.sourceId)!;
      assert(!mid.hidden);
      assert(Math.abs(mid.dx)+Math.abs(mid.dy)>1,'Packet should move');
      assert.equal(final.get(item.sourceId)?.hidden,true,'Packet should be hidden after its journey');
      moving.push({step:k+1,spid:item.sourceId,midpoint:[mid.dx,mid.dy]});
    }
  }
  if(i===2) {
    // Both RTP arrows must be visible while talking and disappear on BYE.
    const exitItems=steps[2].items.filter(t=>t.item.effect==='fadeOut');
    assert.equal(exitItems.length,3);
    const talk=computeNodeStates(steps,2,null,720,1280);
    const bye=computeNodeStates(steps,3,null,720,1280);
    for(const {item} of exitItems) {
      assert.equal(talk.get(item.sourceId)?.hidden,false);
      assert.equal(bye.get(item.sourceId)?.hidden,true);
    }
  }
  verification.push({page:i+8,clicks:steps.length,animations:animations.length,motionPaths:moving.length,
    stepDurationsMs:steps.map(s=>s.totalMs),moving});
  const bundle=copySlide(scenario,i);
  assert(bundle);
  assert(pasteSlide(base,6+i,bundle,{keepSourceFormatting:true}));
}
const output=await savePptx(base);
const reopened=await openPptx(output);
assert.equal(reopened.deck.slides.length,28);
const untouched=await openPptx(original);
for(let i=0;i<25;i++) {
  const oldSlide=untouched.deck.slides[i];
  const newSlide=reopened.deck.slides[i<7?i:i+3];
  assert.equal(reopened.archive.readText(newSlide.path),untouched.archive.readText(oldSlide.path),
    `Original slide ${i+1} changed`);
}
for(let i=0;i<3;i++) {
  assert.deepEqual(getSlideAnimations(reopened.deck.slides[i+7]),getSlideAnimations(scenario.deck.slides[i]));
}
assert.equal(createHash('sha256').update(await readFile(source)).digest('hex'),originalHash);
await writeFile(out,output,{flag:'wx'});
const report={engine:'GenOffice',source,sourceSHA256:originalHash,output:out,originalSlidesPreserved:25,
  totalSlides:28,animationSlides:verification,checks:['native timing round-trip','click groups','hidden entrance',
  'packet motion','packet exit','RTP removal on BYE','original slide XML preserved','source hash unchanged']};
await writeFile(join(root,'metadata/verification.json'),JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify({...report,animationSlides:verification.map(({moving,...v})=>v)},null,2));
