/* Actual Edge pointer/export roundtrip with a synthetic temporary original. */
const fs=require('fs'),path=require('path'),os=require('os'),cp=require('child_process');
const {chromium}=require('C:/Users/Administrator/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const ROOT=path.resolve(__dirname,'..');
const PY='C:/Users/Administrator/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe';
const OUT=path.resolve(process.argv[2]||path.join(ROOT,'records/validation/2026-11-11-geometry-editor'));
function check(value,message){if(!value)throw Error(message)}
function python(args){const r=cp.spawnSync(PY,['-B',...args],{cwd:ROOT,encoding:'utf8'});check(r.status===0,r.stdout+r.stderr);return r.stdout}
(async()=>{
 if(fs.existsSync(path.join(OUT,'browser.json'))||fs.existsSync(path.join(OUT,'synthetic-browser.png')))throw Error('Preserve prior browser evidence; choose a fresh output directory');
 fs.mkdirSync(OUT,{recursive:true});
 const temp=fs.mkdtempSync(path.join(os.tmpdir(),'skirt-geometry-'));
 const fixture=path.join(temp,'fixture.py');
 fs.writeFileSync(fixture,`from pathlib import Path\nfrom PIL import Image,ImageDraw\nimport json,hashlib\np=Path(__file__).parent\nim=Image.new('RGB',(600,360),'white');d=ImageDraw.Draw(im);d.text((20,15),'SYNTHETIC GEOMETRY TEST IMAGE',fill='black');d.rectangle((150,80,450,260),outline='black');im.save(p/'source.png')\nrow=dict(sample_id='synthetic-browser',garment_group_id='synthetic-group',split='development_validation',original_path='source.png',image_sha256=hashlib.sha256((p/'source.png').read_bytes()).hexdigest())\n(p/'inventory.json').write_text(json.dumps([row]))\n`);
 python([fixture]);
 python(['tools/geometry_annotation.py','build','--inventory',path.join(temp,'inventory.json'),'--sample-id','synthetic-browser','--source-root',temp,'--output',path.join(temp,'editor.html')]);
 const browser=await chromium.launch({channel:'msedge',headless:true});let report;
 try{
  const context=await browser.newContext({viewport:{width:1440,height:1050},acceptDownloads:true});
  const page=await context.newPage();let external=0;page.on('request',req=>{if(/^https?:/.test(req.url()))external++});
  await page.goto('file:///'+path.join(temp,'editor.html').replaceAll('\\','/'));
  await page.waitForFunction(()=>document.querySelector('#dimensions').textContent.includes('600 × 360'));
  check(await page.locator('#download').isDisabled(),'Unattested empty draft export enabled');
  await page.locator('#reviewer').fill('Synthetic browser agent');await page.locator('#actor').selectOption('agent');
  await page.locator('#notes').fill('Synthetic pointer/export check only; no human or physical measurements.');await page.locator('#viewed').check();
  await page.locator('#reviewDate').fill('2026-11-11');
  async function drag(axis,low,high){await page.locator('#axis').selectOption(axis);const b=await page.locator('#canvas').boundingBox();await page.mouse.move(b.x+b.width*.5,b.y+low*b.height/360);await page.mouse.down();await page.mouse.move(b.x+b.width*.5,b.y+high*b.height/360);await page.mouse.up()}
  await drag('waist_y',75,85);await drag('hem_y',255,265);
  await page.locator('#axis').selectOption('waist_y');
  const canvasBounds=await page.locator('#canvas').boundingBox();
  await page.mouse.move(canvasBounds.x+canvasBounds.width*.5,canvasBounds.y+120*canvasBounds.height/360);
  await page.mouse.down();
  check(await page.locator('#download').isDisabled(),'Incomplete gesture allowed draft export');
  await page.locator('#canvas').dispatchEvent('pointercancel');await page.mouse.up();
  check(await page.locator('#low').inputValue()==='75'&&await page.locator('#high').inputValue()==='85','Cancelled gesture changed an existing band');
  await page.locator('#axis').selectOption('floor_y');await page.locator('#visibility').selectOption('hidden');
  await page.locator('#axis').selectOption('hem_y');
  await page.locator('#low').fill('300');await page.locator('#high').fill('260');
  check(await page.locator('#download').isDisabled(),'Reversed numeric interval enabled export');
  await page.locator('#low').fill('255');await page.locator('#high').fill('265');
  const pending=page.waitForEvent('download');await page.locator('#download').click();const download=await pending;
  const file=path.join(temp,'draft.json');await download.saveAs(file);
  const draft=JSON.parse(fs.readFileSync(file,'utf8'));
  check(draft.observations.waist_y.interval.join(',')==='75,85','Pointer transform did not preserve source y');
  check(draft.observations.hem_y.interval.join(',')==='255,265','Numeric controls changed source interval');
  check(draft.observations.floor_y.visibility==='hidden'&&draft.observations.floor_y.interval===null,'Hidden reference not preserved');
  check(!draft.reviewed&&!draft.evaluator_approved,'Export gained evaluator approval');
  check(draft.review_date==='2026-11-11','Explicit local observation date changed');
  const validation=JSON.parse(python(['tools/geometry_annotation.py','validate','--draft',file,'--inventory',path.join(temp,'inventory.json'),'--source-root',temp]));
  check(validation.status==='valid_pending_draft','Browser output failed actual Python validation');
  check(external===0,'Offline editor made network requests');
  await page.screenshot({path:path.join(OUT,'synthetic-browser.png'),fullPage:true});
  report={status:'passed_synthetic_browser_roundtrip',original_size:[600,360],waist_y:draft.observations.waist_y,hem_y:draft.observations.hem_y,floor_y:draft.observations.floor_y,python_validation:validation,external_network_requests:external,production_observations_created:0,owned_server_started:false};
  await context.close();
 }finally{await browser.close();const target=path.resolve(temp),base=path.resolve(os.tmpdir());check(path.dirname(target)===base&&path.basename(target).startsWith('skirt-geometry-'),'Unsafe temporary cleanup target');fs.rmSync(target,{recursive:true,force:true})}
 fs.writeFileSync(path.join(OUT,'browser.json'),JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify(report));
})().catch(e=>{console.error(e);process.exitCode=1});
