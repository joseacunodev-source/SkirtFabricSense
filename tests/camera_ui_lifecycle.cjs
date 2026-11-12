const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const code=fs.readFileSync(process.argv[2]||'app/static/index.html','utf8').split('<script>')[1].split('</script>')[0];
const flush=async()=>{for(let i=0;i<12;i++)await Promise.resolve()};
function deferred(){let resolve,reject;return {promise:new Promise((r,j)=>{resolve=r;reject=j}),resolve:v=>resolve(v),reject:e=>reject(e)}}
function source(){const track={stopped:false,stop(){this.stopped=true},getSettings(){return {deviceId:'test'}}};return {track,stream:{getTracks:()=>[track],getVideoTracks:()=>[track]}}}
const result={style:{status:'provisional',label:'pleated',score:.947,reason:'Experimental'},fabric:{status:'unavailable',reason:'No fabric model'},length:{status:'estimate',label:'midi',reason:'Reference supplied'}};
function fixture(getUserMedia,handler=async url=>url==='/api/live'?{id:'job-1'}:{state:'complete',result},motion={}){
 const nodes={};for(const id of ['stateText','state','video','empty','resolution','stop','start','device','message','fabricEnabled','fabricToggleText','fabricValue','fabricReason','styleValue','styleReason','scoreValue','scoreReason','lengthValue','lengthReason','presentation','framingHint','captureMode'])nodes[id]={value:'',textContent:'',disabled:false,hidden:false,classList:{toggle(){}},replaceChildren(){},add(){},play:async()=>{},videoWidth:640,videoHeight:480};
 nodes.presentation.value='worn';nodes.fabricEnabled.checked=true;
 const events={},timers=new Map(),calls=[],animations=[],cancellations=[];let time=0,next=1,mediaChange;
 const media={matches:motion.reduced===true,addEventListener:(event,fn)=>{if(event==='change')mediaChange=fn}};
 const window={addEventListener:(name,fn)=>events[name]=fn};
 if(motion.api)window.matchMedia=()=>media;
 if(motion.api)for(const id of ['styleValue','lengthValue','fabricValue','scoreValue']){
  let current=[];nodes[id].getAnimations=()=>current;
  nodes[id].animate=(frames,options)=>{animations.push({id,frames,options});const animation={cancel:()=>{cancellations.push(id);current=[]}};current=[animation];return animation};
 }
 const context={document:{getElementById:id=>nodes[id],createElement:()=>({getContext:()=>({drawImage(){}}),toDataURL:()=>{time+=motion.encodeDelay||0;return 'data:image/jpeg;base64,'+(motion.image||'frame')}})},navigator:{mediaDevices:{getUserMedia,enumerateDevices:async()=>[]}},window,Option:function(label,value){this.value=value},AbortController,performance:{now:()=>time},setTimeout:(fn,delay)=>{const id=next++;timers.set(id,{fn,at:time+delay});return id},clearTimeout:id=>timers.delete(id),fetch:async(url,options={})=>{calls.push({url,options});const body=await handler(url,options);return {ok:true,json:async()=>body}}};
 vm.createContext(context);vm.runInContext(code,context);
 return {nodes,events,calls,animations,cancellations,render:value=>{context.fixtureResult=value;vm.runInContext('renderResult(fixtureResult)',context)},clear:()=>vm.runInContext('clearResults()',context),reduce:()=>{media.matches=true;mediaChange?.({matches:true})},run:()=>vm.runInContext('analyzeFrame()',context),noSchedule:()=>vm.runInContext('clearTimeout(timer)',context),setTime:value=>time=value,tick:async value=>{time=value;for(const [id,t] of [...timers])if(t.at<=time){timers.delete(id);t.fn()}await flush()}};
}
(async()=>{
 // Requested modes are ideals; actual decoded dimensions are shown, never assumed.
 let requests=[],s=source(),f=fixture(async constraints=>{requests.push(constraints);return s.stream});f.nodes.captureMode.value='1080';await f.nodes.start.onclick();assert.deepEqual(JSON.parse(JSON.stringify(requests[0])),{audio:false,video:{width:{ideal:1920},height:{ideal:1080}}});assert.match(f.nodes.resolution.textContent,/640 \u00d7 480 px \(actual\)/);await f.run();f.nodes.captureMode.value='2160';f.nodes.captureMode.onchange();assert.equal(s.track.stopped,true);assert.equal(f.nodes.styleValue.textContent,'\u2014');assert.match(f.nodes.message.textContent,/Start the camera again/);
 // Rejected constraints fall back to automatic, but device selection remains exact.
 requests=[];s=source();f=fixture(async c=>{requests.push(c);if(requests.length===1)throw Object.assign(Error('unsupported'),{name:'OverconstrainedError'});return s.stream});f.nodes.device.value='camera-1';f.nodes.captureMode.value='2160';await f.nodes.start.onclick();assert.equal(requests.length,2);assert.deepEqual(JSON.parse(JSON.stringify(requests[1])),{audio:false,video:{deviceId:{exact:'camera-1'}}});assert.match(f.nodes.message.textContent,/using automatic/);
 // A 4K request within the frame and transport limits still submits one native-size frame.
 requests=[];s=source();f=fixture(async c=>{requests.push(c);return s.stream});f.nodes.captureMode.value='2160';f.nodes.video.videoWidth=3840;f.nodes.video.videoHeight=2160;await f.nodes.start.onclick();assert.deepEqual(JSON.parse(JSON.stringify(requests[0].video)),{width:{ideal:3840},height:{ideal:2160}});await f.run();assert.equal(f.calls.filter(c=>c.url==='/api/live').length,1);assert.match(f.nodes.resolution.textContent,/3840 \u00d7 2160 px/);f.nodes.stop.onclick();
 // An old fallback stream cannot revive a changed or stopped camera.
 let fallbackGate=deferred();requests=[];f=fixture(async c=>{requests.push(c);if(requests.length===1)throw Object.assign(Error('unsupported'),{name:'OverconstrainedError'});return fallbackGate.promise});f.nodes.captureMode.value='720';let fallbackPending=f.nodes.start.onclick();await flush();f.nodes.captureMode.onchange();s=source();fallbackGate.resolve(s.stream);await fallbackPending;assert.equal(s.track.stopped,true);assert.equal(f.nodes.stateText.textContent,'Camera off');
 // Oversize dimensions and encoded bodies are rejected without any upload.
 s=source();f=fixture(async()=>s.stream);await f.nodes.start.onclick();f.nodes.video.videoWidth=6000;f.nodes.video.videoHeight=4000;await f.run();assert.equal(f.calls.length,0);assert.match(f.nodes.message.textContent,/20 megapixels/);assert.equal(f.nodes.styleValue.textContent,'\u2014');f.nodes.stop.onclick();
 s=source();f=fixture(async()=>s.stream,undefined,{image:'A'.repeat(16*1024*1024)});await f.nodes.start.onclick();await f.run();assert.equal(f.calls.length,0);assert.match(f.nodes.message.textContent,/too large/);assert.equal(f.nodes.styleValue.textContent,'\u2014');f.nodes.stop.onclick();
 // A synchronous encode that consumes the frame-age budget never uploads a stale frame.
 s=source();f=fixture(async()=>s.stream,undefined,{encodeDelay:1001});await f.nodes.start.onclick();await f.run();assert.equal(f.calls.length,0);assert.match(f.nodes.message.textContent,/expired during encoding/);assert.equal(f.nodes.styleValue.textContent,'\u2014');f.nodes.stop.onclick();
 // Renegotiated dimensions invalidate the previous result.
 s=source();f=fixture(async()=>s.stream);await f.nodes.start.onclick();await f.run();f.nodes.video.videoWidth=1280;f.nodes.video.videoHeight=720;f.nodes.video.onresize();assert.equal(f.nodes.styleValue.textContent,'\u2014');assert.match(f.nodes.resolution.textContent,/1280 \u00d7 720 px/);f.nodes.stop.onclick();
 s=source();f=fixture(async()=>s.stream);assert.match(f.nodes.framingHint.textContent,/waist, hem, feet and floor/);await f.nodes.start.onclick();assert.equal(f.nodes.stateText.textContent,'Camera on');assert.equal(f.nodes.video.hidden,false);f.nodes.stop.onclick();assert.equal(s.track.stopped,true);assert.equal(f.nodes.video.srcObject,null);
 let gate=deferred();f=fixture(()=>gate.promise);let pending=f.nodes.start.onclick();f.nodes.stop.onclick();s=source();gate.resolve(s.stream);await pending;assert.equal(s.track.stopped,true);assert.equal(f.nodes.stateText.textContent,'Camera off');
 f=fixture(async()=>{throw Object.assign(new Error('denied'),{name:'NotAllowedError'})});await f.nodes.start.onclick();assert.match(f.nodes.message.textContent,/permission was denied/);assert.equal(f.nodes.start.disabled,false);
 s=source();f=fixture(async()=>s.stream);await f.nodes.start.onclick();s.track.onended();assert.equal(f.nodes.video.srcObject,null);assert.match(f.nodes.message.textContent,/disconnected/);
 s=source();f=fixture(async()=>s.stream);await f.nodes.start.onclick();f.events.pagehide();assert.equal(s.track.stopped,true);
 // Correct backend state key, independent attributes and source options.
 s=source();f=fixture(async()=>s.stream);await f.nodes.start.onclick();f.nodes.presentation.value='held';await f.run();assert.equal(f.nodes.styleValue.textContent,'pleated');assert.equal(f.nodes.lengthValue.textContent,'midi');assert.match(f.nodes.lengthReason.textContent,/Estimated/);assert.equal(f.nodes.fabricValue.textContent,'—');assert.deepEqual(JSON.parse(f.calls[0].options.body),{image_base64:'frame',fabric_enabled:true,presentation:'held'});
 // Acquired-frame expiry also clears a completed result without another frame.
 f.noSchedule();await f.tick(1000);assert.equal(f.nodes.styleValue.textContent,'—');assert.match(f.nodes.styleReason.textContent,/expired/);
 // New acquisition clears old evidence while its request remains outstanding.
 s=source();let gate2=deferred(),posts=0;f=fixture(async()=>s.stream,async url=>url==='/api/live'?(++posts===1?{id:'first'}:gate2.promise):{state:'complete',result});await f.nodes.start.onclick();await f.run();assert.equal(f.nodes.styleValue.textContent,'pleated');pending=f.run();assert.equal(f.nodes.styleValue.textContent,'—');f.nodes.stop.onclick();gate2.resolve({id:'late'});await pending;assert.ok(f.calls.some(c=>c.url==='/api/jobs/cancel'&&JSON.parse(c.options.body).id==='late'));assert.equal(f.nodes.styleValue.textContent,'—');
 // A late completion is rejected even when timer callbacks are delayed.
 s=source();gate=deferred();f=fixture(async()=>s.stream,async url=>url==='/api/live'?{id:'slow'}:gate.promise);await f.nodes.start.onclick();pending=f.run();await flush();f.setTime(1001);gate.resolve({state:'complete',result});await pending;assert.equal(f.nodes.styleValue.textContent,'—');
 // Settings changes cancel old work; responses cannot overwrite new settings.
 for(const setting of ['fabric','presentation']){
  s=source();gate=deferred();f=fixture(async()=>s.stream,async url=>url==='/api/live'?{id:'old'}:url==='/api/jobs/cancel'?{}:gate.promise);await f.nodes.start.onclick();pending=f.run();await flush();
  if(setting==='fabric'){f.nodes.fabricEnabled.checked=false;f.nodes.fabricEnabled.onchange();assert.equal(f.nodes.fabricValue.textContent,'Off')}else{f.nodes.presentation.value='hanging';f.nodes.presentation.onchange();assert.match(f.nodes.framingHint.textContent,/not the person holding it/)}
  gate.resolve({state:'complete',result});await pending;assert.equal(f.nodes.styleValue.textContent,'—');assert.ok(f.calls.some(c=>c.url==='/api/jobs/cancel'));if(setting==='fabric')assert.equal(f.nodes.fabricValue.textContent,'Off');
 }
 // Muting invalidates outstanding evidence, and unmuting allows acquisition.
 s=source();f=fixture(async()=>s.stream);await f.nodes.start.onclick();await f.run();s.track.onmute();assert.equal(f.nodes.styleValue.textContent,'—');assert.equal(f.nodes.stateText.textContent,'Camera interrupted');const before=f.calls.length;await f.run();assert.equal(f.calls.length,before);s.track.onunmute();await f.run();assert.equal(f.nodes.styleValue.textContent,'pleated');
 // A mute event during startup must survive the pending playback continuation.
 s=source();gate=deferred();f=fixture(async()=>s.stream);f.nodes.video.play=()=>gate.promise;let indicator=false;f.nodes.state.classList.toggle=(name,on)=>{if(name==='on')indicator=on};pending=f.nodes.start.onclick();await flush();s.track.onmute();assert.equal(f.nodes.stateText.textContent,'Camera interrupted');gate.resolve();await pending;assert.equal(f.nodes.stateText.textContent,'Camera interrupted');assert.equal(indicator,false);await f.tick(0);await f.run();assert.equal(f.calls.length,0);s.track.onunmute();await f.tick(0);assert.equal(f.nodes.stateText.textContent,'Camera on');assert.equal(indicator,true);assert.equal(f.nodes.styleValue.textContent,'pleated');
 // A stream already muted on acquisition may not emit a new mute event.
 s=source();s.track.muted=true;f=fixture(async()=>s.stream);await f.nodes.start.onclick();assert.equal(f.nodes.stateText.textContent,'Camera interrupted');await f.tick(0);await f.run();assert.equal(f.calls.length,0);s.track.muted=false;s.track.onunmute();await f.tick(0);assert.equal(f.nodes.stateText.textContent,'Camera on');assert.equal(f.nodes.styleValue.textContent,'pleated');
 // Stopping during playback keeps late mute/unmute/play callbacks inactive.
 s=source();gate=deferred();f=fixture(async()=>s.stream);f.nodes.video.play=()=>gate.promise;pending=f.nodes.start.onclick();await flush();s.track.onmute();f.nodes.stop.onclick();s.track.onunmute();gate.resolve();await pending;await f.tick(0);assert.equal(f.nodes.stateText.textContent,'Camera off');assert.equal(s.track.stopped,true);assert.equal(f.calls.length,0);
 // A stalled transport is aborted at acquisition age, not after an 8 s request timeout.
 s=source();f=fixture(async()=>s.stream,(url,options)=>new Promise((resolve,reject)=>options.signal.addEventListener('abort',()=>reject(Object.assign(Error('aborted'),{name:'AbortError'})))));await f.nodes.start.onclick();pending=f.run();await flush();f.noSchedule();await f.tick(1000);await pending;assert.equal(f.calls[0].options.signal.aborted,true);assert.equal(f.nodes.styleValue.textContent,'—');
 // Pending polling keeps one submission in flight and eventually renders completion.
 s=source();let polls=0;f=fixture(async()=>s.stream,async url=>url==='/api/live'?{id:'pending'}:{state:++polls===1?'pending':'complete',result});await f.nodes.start.onclick();pending=f.run();await flush();await f.run();assert.equal(f.calls.filter(c=>c.url==='/api/live').length,1);f.noSchedule();await f.tick(200);await pending;assert.equal(f.nodes.styleValue.textContent,'pleated');assert.equal(polls,2);
 // Playback failure must clear any result produced by an early unmute event.
 s=source();gate=deferred();f=fixture(async()=>s.stream);f.nodes.video.play=()=>gate.promise;pending=f.nodes.start.onclick();await flush();s.track.onunmute();await f.tick(0);assert.equal(f.nodes.styleValue.textContent,'pleated');assert.equal(f.nodes.scoreValue.textContent,'94.7%');gate.reject(Error('Playback failed'));await pending;assert.equal(f.nodes.stateText.textContent,'Camera unavailable');assert.equal(f.nodes.styleValue.textContent,'—');assert.equal(f.nodes.scoreValue.textContent,'—');assert.equal(s.track.stopped,true);const failedCalls=f.calls.length;s.track.onunmute();s.track.onended();await f.tick(0);assert.equal(f.calls.length,failedCalls);assert.equal(f.nodes.stateText.textContent,'Camera unavailable');assert.equal(f.nodes.message.textContent,'Playback failed');
 // Model scores are current pleating evidence, never measured accuracy or length confidence.
 for(const score of [0,.947,1]){
  s=source();f=fixture(async()=>s.stream,async url=>url==='/api/live'?{id:'score'}:{state:'complete',result:{...result,style:{...result.style,score}}});await f.nodes.start.onclick();await f.run();assert.equal(f.nodes.scoreValue.textContent,(score*100).toFixed(1)+'%');assert.match(f.nodes.scoreReason.textContent,/not measured accuracy/);
  f.noSchedule();await f.tick(1000);assert.equal(f.nodes.scoreValue.textContent,'—');
 }
 for(const style of [
  ...[null,undefined,'0.9',true,false,NaN,Infinity,-.1,1.1].map(score=>({...result.style,score})),
  {status:'unavailable',label:'pleated',score:.9},{status:'uncertain',label:'pleated',score:.9},
  {status:'provisional',label:' ',score:.9},null,
 ]){
  s=source();f=fixture(async()=>s.stream,async url=>url==='/api/live'?{id:'bad-score'}:{state:'complete',result:{...result,style}});await f.nodes.start.onclick();await f.run();assert.equal(f.nodes.scoreValue.textContent,'—');
 }
 // Every lifecycle invalidation clears the newly displayed score too.
 for(const action of ['stop','mute','presentation','fabric','new frame']){
  s=source();gate=deferred();posts=0;f=fixture(async()=>s.stream,async url=>url==='/api/live'?(++posts===1?{id:'first-score'}:gate.promise):{state:'complete',result});await f.nodes.start.onclick();await f.run();assert.equal(f.nodes.scoreValue.textContent,'94.7%');
  if(action==='stop')f.nodes.stop.onclick();else if(action==='mute')s.track.onmute();else if(action==='presentation'){f.nodes.presentation.value='hanging';f.nodes.presentation.onchange()}else if(action==='fabric'){f.nodes.fabricEnabled.checked=false;f.nodes.fabricEnabled.onchange()}else{pending=f.run();f.nodes.stop.onclick();gate.resolve({id:'late-score'});await pending}
  assert.equal(f.nodes.scoreValue.textContent,'—');
 }
 // Motion is restricted to changed supported labels; scores never bounce per frame.
 f=fixture(async()=>source().stream,undefined,{api:true});f.render(result);assert.deepEqual(f.animations.map(a=>a.id),['styleValue','lengthValue']);assert.ok(f.animations.every(a=>a.options.duration===180));f.render(result);assert.equal(f.animations.length,2);f.clear();assert.equal(f.nodes.styleValue.textContent,'—');f.render(result);assert.equal(f.animations.length,2);f.render({...result,style:{...result.style,label:'non_pleated'}});assert.equal(f.animations.length,3);
 // An explicit invalidation resets the reveal history without retaining old text.
 f=fixture(async()=>source().stream,undefined,{api:true});f.render(result);f.nodes.presentation.onchange();assert.equal(f.nodes.styleValue.textContent,'—');assert.equal(f.nodes.scoreValue.textContent,'—');assert.ok(f.cancellations.includes('styleValue'));f.render(result);assert.equal(f.animations.length,4);
 // A live reduced-motion preference cancels current effects and suppresses new ones.
 f=fixture(async()=>source().stream,undefined,{api:true});f.render(result);f.reduce();assert.equal(f.cancellations.length,2);f.render({...result,style:{...result.style,label:'non_pleated'}});assert.equal(f.animations.length,2);assert.equal(f.nodes.styleValue.textContent,'non pleated');
 f=fixture(async()=>source().stream,undefined,{api:true,reduced:true});f.render(result);assert.equal(f.animations.length,0);assert.equal(f.nodes.scoreValue.textContent,'94.7%');
 // Missing or failed optional animation APIs cannot block results or immediate clearing.
 f=fixture(async()=>source().stream);f.render(result);assert.equal(f.nodes.styleValue.textContent,'pleated');f.clear();assert.equal(f.nodes.styleValue.textContent,'—');
 f=fixture(async()=>source().stream,undefined,{api:true});f.nodes.styleValue.animate=()=>{throw Error('Unsupported animation')};f.nodes.lengthValue.getAnimations=()=>{throw Error('Animation inspection unavailable')};f.render(result);assert.equal(f.nodes.styleValue.textContent,'pleated');assert.equal(f.nodes.scoreValue.textContent,'94.7%');f.clear();assert.equal(f.nodes.styleValue.textContent,'—');assert.equal(f.nodes.lengthValue.textContent,'—');
 console.log('18 camera/live-loop scenarios, 21 score cases, 6 motion cases and 7 camera-mode/safety cases passed (mock APIs only)');
})().catch(e=>{console.error(e);process.exitCode=1});
