/* Browser geometry checks of real HTML; camera and inference remain off. */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const http = require('node:http');
const path = require('node:path');
const crypto = require('node:crypto');
const {chromium} = require('C:/Users/Administrator/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const root = path.resolve(__dirname,'..');
const output = path.resolve(process.argv[2] || path.join(root,'records/validation/2026-11-11-compact-layout'));
const source = fs.readFileSync(path.join(root,'app/static/index.html'));
const sha = bytes=>crypto.createHash('sha256').update(bytes).digest('hex');
async function main(){
 if(fs.existsSync(path.join(output,'browser.json')))throw Error('Preserve existing report; use a new output directory');
 fs.mkdirSync(output,{recursive:true});
 const server=http.createServer((req,res)=>{
  if(req.url!=='/'){res.writeHead(404);res.end();return}
  res.writeHead(200,{'Content-Type':'text/html; charset=utf-8'});res.end(source);
 });
 await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
 const browser=await chromium.launch({channel:'msedge',headless:true});
 const scenarios=[];let cameraRequests=0;
 try{
  const context=await browser.newContext({viewport:{width:800,height:480},reducedMotion:'reduce'});
  await context.addInitScript(()=>{
   window.captureCalls=0;
   if(navigator.mediaDevices)navigator.mediaDevices.getUserMedia=()=>{window.captureCalls++;throw Error('No camera is used in layout checks')};
  });
  const page=await context.newPage();
  await page.goto(`http://127.0.0.1:${server.address().port}/`,{waitUntil:'networkidle'});
  async function inspect(name){
   const values=await page.evaluate(()=>{
    const selectors=['.camera','#start','#stop','#device','#presentation','#captureMode',
     '#styleValue','#lengthValue','#fabricValue','#scoreValue','.switch'];
    const bounds=Object.fromEntries(selectors.map(s=>{
     const e=document.querySelector(s),r=e.getBoundingClientRect();return[s,{x:r.x,y:r.y,width:r.width,height:r.height,right:r.right,bottom:r.bottom,display:getComputedStyle(e).display}];
    }));
    return {bounds,viewport:[innerWidth,innerHeight],horizontalOverflow:document.documentElement.scrollWidth>innerWidth,
     cameraState:document.querySelector('#stateText').textContent,videoHidden:document.querySelector('#video').hidden,
     captureCalls:window.captureCalls,labels:[...document.querySelectorAll('.hemline-list li')].map(e=>e.textContent),
     modes:[...document.querySelector('#presentation').options].map(e=>e.value)};
   });
   assert.equal(values.horizontalOverflow,false,name+' horizontal overflow');
   for(const [selector,b]of Object.entries(values.bounds)){
    assert.ok(b.width>0&&b.height>0,name+' '+selector+' has dimensions');
    assert.ok(b.x>=-1&&b.right<=values.viewport[0]+1,name+' '+selector+' is within viewport horizontally');
    if(values.viewport[0]===800)assert.ok(b.y>=0&&b.bottom<=480,name+' '+selector+' is visible without page scrolling: '+JSON.stringify(b));
   }
   if(values.viewport[0]===800){
    for(const s of ['#start','#stop','#device','#presentation','#captureMode','.switch'])assert.ok(values.bounds[s].height>=44,name+' '+s+' touch height');
    assert.ok(values.bounds['.camera'].height>=200,'Camera preview remains at least200 CSS pixels high');
   }
   assert.deepEqual(values.labels,['Micro','Mini','Above knee','On knee','Below knee','Midi','Tea','Maxi','Full']);
   assert.deepEqual(values.modes,['worn','hanging','mannequin','held']);
   assert.equal(values.captureCalls,0);assert.equal(values.videoHidden,true);
   scenarios.push({name,...values});return values;
  }
  await inspect('compact_camera_off');
  await page.screenshot({path:path.join(output,'camera-off-800x480.png')});
  // Settings remain reachable; changing presentation does not start a camera.
  await page.selectOption('#captureMode','1080');
  await page.selectOption('#presentation','held');
  await page.locator('.switch').click();
  await inspect('compact_settings_changed');
  assert.equal(await page.locator('#fabricValue').innerText(),'Off');
  await page.selectOption('#presentation','worn');
  await page.locator('.switch').click();
  // Synthetic text only: exercises actual rendering without implying a captured prediction.
  await page.evaluate(()=>renderResult({
   style:{status:'provisional',label:'non_pleated',score:.81,reason:'Synthetic layout check only. Not a camera result.'},
   length:{status:'unavailable',reason:'A matching calibrated body reference is required before assigning a hemline category.'},
   fabric:{status:'unavailable',reason:'Texture detail is insufficient for a supported appearance estimate.'}
  }));
  await inspect('compact_synthetic_attribute_text');
  await page.evaluate(()=>clearResults());
  const summary=page.locator('.reference summary');
  await summary.focus();await page.keyboard.press('Enter');
  assert.equal(await page.locator('.reference').getAttribute('open'),'');
  assert.equal(await page.locator('.hemline-list li').count(),9);
  await page.keyboard.press('Enter');
  assert.equal(await page.locator('.reference').getAttribute('open'),null);
  await page.locator('.framing-details summary').focus();await page.keyboard.press('Enter');
  assert.ok(await page.locator('#framingHint').isVisible());
  await page.locator('.framing-details summary').press('Enter');
  await page.evaluate(()=>scrollTo(0,0));
  await inspect('compact_disclosures_closed_again');
  await page.setViewportSize({width:1440,height:1080});
  await page.reload({waitUntil:'networkidle'});
  await inspect('desktop_camera_off');
  await page.screenshot({path:path.join(output,'camera-off-desktop.png'),fullPage:true});
  await page.setViewportSize({width:390,height:844});
  await inspect('portrait_390_no_horizontal_overflow');
  cameraRequests=await page.evaluate(()=>window.captureCalls);
  await context.close();
 }finally{
  await browser.close();await new Promise(resolve=>server.close(resolve));
 }
 const report={date:'2026-11-11',status:'passed_browser_layout_checks',html_sha256:sha(source),
  source:'app/static/index.html',browser:'Existing Microsoft Edge via bundled Playwright',scenarios,
  keyboard_disclosures_checked:true,camera_requests:cameraRequests,test_server_stopped:true,
  physical_lcd_tested:false,pi_verified:false,synthetic_text_is_not_prediction_evidence:true};
 fs.writeFileSync(path.join(output,'browser.json'),JSON.stringify(report,null,2)+'\n');
 console.log(JSON.stringify({status:report.status,scenarios:scenarios.length,camera_requests:cameraRequests,output}));
}
main().catch(e=>{console.error(e);process.exitCode=1});
