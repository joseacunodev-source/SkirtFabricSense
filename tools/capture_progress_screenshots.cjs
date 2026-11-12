/* Genuine browser captures of the selected station and literal code excerpts. */
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const { chromium } = require('C:/Users/Administrator/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const root = path.resolve(__dirname, '..');
const out = path.join(root, 'output/progress_report_2026-11-11');
const sha = b => crypto.createHash('sha256').update(b).digest('hex');
const esc = s => s.replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;');
async function main() {
  if (fs.existsSync(out)) throw Error('Preserve existing output; choose a new version');
  fs.mkdirSync(out, {recursive:true});
  const browser = await chromium.launch({channel:'msedge',headless:true});
  const captures = [];
  try {
    const context = await browser.newContext({viewport:{width:1440,height:1080},deviceScaleFactor:1});
    const page = await context.newPage();
    await page.goto('http://127.0.0.1:8766/',{waitUntil:'networkidle'});
    await page.evaluate(() => document.fonts.ready);
    const served = await (await context.request.get('http://127.0.0.1:8766/')).body();
    const source = 'artifacts/stations/skirt-research-station-v8/application/app/static/index.html';
    if (sha(served)!==sha(fs.readFileSync(path.join(root,source)))) throw Error('Served UI differs from selected station');
    await page.screenshot({path:path.join(out,'01_current_camera_ui_desktop.png'),fullPage:true});
    captures.push({file:'01_current_camera_ui_desktop.png',kind:'unaltered_browser_screenshot',source,source_sha256:sha(served),camera_started:false,viewport:[1440,1080]});
    await page.setViewportSize({width:800,height:480});
    await page.screenshot({path:path.join(out,'02_current_camera_ui_800x480.png'),fullPage:false});
    captures.push({file:'02_current_camera_ui_800x480.png',kind:'unaltered_browser_screenshot',source,source_sha256:sha(served),camera_started:false,viewport:[800,480],physical_lcd_test:false});
    const snippets = [
      ['03_code_training.png','tools/training/train_skirt_baseline.py',140,167,'Transfer learning and GPU execution check'],
      ['04_code_frame_freshness.png','app/live_state.py',116,145,'Discarding stale inference results'],
      ['05_code_hemline_rules.png','app/hemline.py',25,53,'Calibrated hemline boundaries and uncertainty'],
    ];
    for (const [file,source,first,last,title] of snippets) {
      const bytes=fs.readFileSync(path.join(root,source));
      const lines=bytes.toString('utf8').split(/\r?\n/).slice(first-1,last);
      const html=`<!doctype html><html><head><meta charset="utf-8"><title>${esc(source)}</title><style>*{box-sizing:border-box}body{margin:0;background:white;color:#20242a;font-family:Arial,sans-serif}header{padding:22px 28px;border-bottom:1px solid #ddd}header strong{font-size:19px}header p{margin:8px 0 0;color:#555;font-size:14px}.rows{padding:20px 20px 24px 0}.row{display:grid;grid-template-columns:66px 1fr;font:16px/1.65 Consolas,'Courier New',monospace}.n{color:#868b91;text-align:right;padding-right:20px;user-select:none}.code{white-space:pre-wrap;overflow-wrap:anywhere;padding-right:25px}footer{border-top:1px solid #ddd;padding:14px 28px;color:#60666c;font-size:13px}</style></head><body><header><strong>${esc(source)}</strong><p>${esc(title)} | Lines ${first}-${last}</p></header><main class="rows">${lines.map((s,i)=>`<div class="row"><span class="n">${first+i}</span><span class="code">${esc(s)||' '}</span></div>`).join('')}</main><footer>SkirtFabricSense source excerpt. Line wrapping is for readability.</footer></body></html>`;
      const htmlfile=file.replace('.png','.html');
      fs.writeFileSync(path.join(out,htmlfile),html);
      await page.setViewportSize({width:1520,height:900});
      await page.goto('file:///'+path.join(out,htmlfile).replaceAll('\\','/'));
      await page.screenshot({path:path.join(out,file),fullPage:true});
      captures.push({file,kind:'browser_rendered_literal_source_excerpt',source,source_sha256:sha(bytes),first_line:first,last_line:last,training_executed_for_capture:false});
    }
    await context.close();
    fs.writeFileSync(path.join(out,'capture-record.json'),JSON.stringify({captured_at:new Date().toISOString(),station:'station-v8 / research-v13',browser:'Microsoft Edge via Playwright',captures,notes:['No generated imagery or fabricated editor interface.','UI screenshots show actual camera-off state.','Code excerpts preserve source text and actual line numbers; these are not IDE screenshots.','No model training, camera access or Raspberry Pi test performed.']},null,2)+'\n');
  } finally {await browser.close();}
  console.log(JSON.stringify({output:out,captures:captures.length}));
}
main().catch(e=>{console.error(e);process.exitCode=1});
