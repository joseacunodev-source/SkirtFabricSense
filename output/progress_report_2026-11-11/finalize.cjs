const fs=require('fs'),path=require('path'),crypto=require('crypto');
const {chromium}=require('C:/Users/Administrator/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
(async()=>{
 const p=__dirname;
 const file=path.join(p,'05_code_hemline_rules.html');
 let html=fs.readFileSync(file,'utf8').replace('Lines 25-57','Lines 25-53');
 html=html.replace(/<div class="row"><span class="n">5[45]<\/span>.*?<\/div>/g,'');
 fs.writeFileSync(file,html);
 const r=JSON.parse(fs.readFileSync(path.join(p,'capture-record.json')));
 r.captures[4].last_line=53;
 const browser=await chromium.launch({channel:'msedge',headless:true});
 try{const page=await browser.newPage({viewport:{width:1520,height:900}});
 await page.goto('file:///'+file.replaceAll('\\','/'));
 await page.screenshot({path:path.join(p,'05_code_hemline_rules.png'),fullPage:true});
 }finally{await browser.close()}
 r.capture_script_sha256=crypto.createHash('sha256').update(fs.readFileSync(path.resolve(p,'../../tools/capture_progress_screenshots.cjs'))).digest('hex');
 fs.writeFileSync(path.join(p,'capture-record.json'),JSON.stringify(r,null,2)+'\n');
})().catch(e=>{console.error(e);process.exitCode=1});
