/* Real browser workflow; server supplied by a temporary synthetic Python fixture. */
const assert = require('assert/strict');
const fs = require('fs'),path = require('path');
const {chromium} = require('C:/Users/Administrator/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
async function main(){
 const [origin,temp]=process.argv.slice(2);
 const browser=await chromium.launch({channel:'msedge',headless:true});
 const errors=[];let checks=0;
 try{
  const context=await browser.newContext({viewport:{width:1360,height:1000},acceptDownloads:true});
  const page=await context.newPage();page.on('pageerror',e=>errors.push(String(e)));
  page.on('dialog',dialog=>dialog.accept());
  await page.goto(origin,{waitUntil:'networkidle'});
  await page.waitForFunction(()=>!document.getElementById('save').disabled);
  assert.equal(await page.locator('#progress').innerText(),'Image 1 of 2');checks++;
  assert.equal(await page.locator('#descriptors').isDisabled(),true);checks++;
  assert.equal(await page.locator('#appearance').inputValue(),'unknown');checks++;
  await page.locator('#reviewer').fill('Synthetic browser actor');
  await page.locator('#actor').selectOption('agent');
  await page.locator('#viewed').check();
  await page.locator('#notes').fill('Synthetic browser fixture observation. Unknown detail; no real garment reviewed.');
  const waiting=page.waitForEvent('download');await page.locator('#download').click();
  const download=await waiting;const exportPath=path.join(temp,'download.json');await download.saveAs(exportPath);
  const payload=JSON.parse(fs.readFileSync(exportPath,'utf8'));
  assert.equal(payload.observations.appearance_status,'unknown');checks++;
  assert.deepEqual(payload.observations.appearance_descriptors,[]);checks++;
  assert.equal(payload.reviewer.actor_kind,'agent');checks++;
  let queue=await(await context.request.get(origin+'/api/queue')).json();
  assert.equal(queue.submitted_events,0);checks++;
  await page.locator('#save').click();
  await page.waitForFunction(()=>document.getElementById('status').textContent.startsWith('Saved as'));
  queue=await(await context.request.get(origin+'/api/queue')).json();assert.equal(queue.submitted_events,1);checks++;
  // Repeat-click must succeed as an idempotent acknowledgement, never a second event.
  await page.locator('#save').click();
  await page.waitForFunction(()=>document.getElementById('status').textContent.includes('No duplicate event'));
  queue=await(await context.request.get(origin+'/api/queue')).json();assert.equal(queue.submitted_events,1);checks++;
  await page.locator('#next').click();await page.waitForFunction(()=>document.getElementById('progress').textContent==='Image 2 of 2'&&!document.getElementById('save').disabled);
  assert.equal(await page.locator('#notes').inputValue(),'');assert.equal(await page.locator('#viewed').isChecked(),false);checks++;
  await page.locator('#association').selectOption('clear');
  await page.locator('#appearance').selectOption('single_appearance');
  await page.locator('#descriptors').fill('Plain synthetic rectangle');
  assert.equal(await page.locator('#descriptors').isDisabled(),false);checks++;
  await page.locator('#association').selectOption('uncertain');
  assert.equal(await page.locator('#appearance').inputValue(),'unknown');assert.equal(await page.locator('#descriptors').inputValue(),'');checks++;
  await page.locator('#viewed').check();await page.locator('#notes').fill('Synthetic second fixture observation with insufficient evidence.');
  await page.locator('#save').click();await page.waitForFunction(()=>document.getElementById('status').textContent.startsWith('Saved as'));
  queue=await(await context.request.get(origin+'/api/queue')).json();assert.equal(queue.submitted_events,2);assert.equal(queue.pending_items,0);checks++;
  await page.screenshot({path:path.join(temp,'browser-synthetic-review.png'),fullPage:true});
  assert.deepEqual(errors,[]);checks++;
  await context.close();
 } finally{await browser.close()}
 console.log(JSON.stringify({checks_passed:checks,synthetic_fixtures_only:true,real_observations_added:0}));
}
main().catch(error=>{console.error(error);process.exitCode=1});
