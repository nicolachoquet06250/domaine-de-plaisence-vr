import assert from 'node:assert/strict';
import { test } from 'node:test';
import { readFileSync } from 'node:fs';
import vm from 'node:vm';
import ts from 'typescript';

const compile = file => ts.transpileModule(readFileSync(new URL(file, import.meta.url),'utf8'), {
  compilerOptions:{ module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2022 },
}).outputText;
const input = {};
vm.runInNewContext(compile('../src/mobile-input.ts'),{exports:input});
const devices = {};
vm.runInNewContext(compile('../src/mobile-device.ts'),{exports:devices});

class Element {
  listeners = new Map(); attrs = {}; style = {}; dataset = {}; captures = new Set();
  classes = new Set();
  classList = {
    contains: name=>this.classes.has(name),
    toggle: (name,on)=>on ? this.classes.add(name) : this.classes.delete(name),
    remove: (...names)=>names.forEach(name=>this.classes.delete(name)),
  };
  addEventListener(name,fn) { if(!this.listeners.has(name))this.listeners.set(name,new Set());this.listeners.get(name).add(fn); }
  removeEventListener(name,fn) { this.listeners.get(name)?.delete(fn); }
  emit(name,event={}) { for(const fn of this.listeners.get(name)??[])fn({currentTarget:this,preventDefault(){},button:0,...event}); }
  setAttribute(name,value) { this.attrs[name]=value; }
  append() {}
  remove() { this.removed=true; }
  setPointerCapture(id) { this.captures.add(id); }
  hasPointerCapture(id) { return this.captures.has(id); }
  releasePointerCapture(id) { this.captures.delete(id);this.emit('lostpointercapture',{pointerId:id}); }
  getBoundingClientRect() { return {left:0,top:0,width:100,height:100}; }
}

function setup(device = {userAgent:'Mozilla/5.0 (Linux; Android 14) Chrome/126.0 Mobile Safari/537.36',platform:'Linux armv8l',maxTouchPoints:5}) {
  const elements=new Map();
  const overlay=new Element();
  overlay.querySelector=selector=>{
    if(!elements.has(selector))elements.set(selector,new Element());
    return elements.get(selector);
  };
  const body=new Element(), doc=new Element(), win=new Element(), media=new Element();
  media.matches=true;
  Object.assign(doc,{body,createElement:()=>overlay});
  let menuOpen=false;
  const comfort={toggle(){menuOpen=!menuOpen;},closeMenu(){menuOpen=false;}};
  const provider={getMoveAxis(out){out.x=out.y=0;return out;}};
  const nativeGet=provider.getMoveAxis;
  const fields={};const root={setProperties(props){Object.assign(fields,props);}};
  const entity={hasComponent:()=>true,setValue(_c,key,value){fields[key]=value;}};
  const xr=new Element();xr.isPresenting=false;
  const renderer={ratio:2,getPixelRatio(){return this.ratio;},setPixelRatio(value){this.ratio=value;}};
  const quaternion={x:0,y:0,setFromEuler(e){this.x=e.x;this.y=e.y;}};
  class Euler {x=0;y=0;setFromQuaternion(q){this.x=q.x;this.y=q.y;}}
  const TurnSystem={},ComfortMenuSystem={};
  const exports={};
  vm.runInNewContext(compile('../src/mobile-controls.ts'),{
    exports,document:doc,window:win,navigator:device,matchMedia:()=>media,location:{search:'?touch=1'},URLSearchParams,devicePixelRatio:3,
    require: name=>{
      if(name==='@iwsdk/core')return {createSystem:()=>class{cleanupFuncs=[];},Euler,TurnSystem,getRequiredInputProvider:(_name,p)=>p,ScreenSpace:{}};
      if(name==='./mobile-input.js')return input;
      if(name==='./mobile-device.js')return devices;
      if(name==='./comfort-menu.js')return {ComfortMenuSystem};
      return {ComfortSettings:{}};
    },
  });
  const system=new exports.MobileControlsSystem();
  const level={arrival:false,subscribe(fn){this.notify=fn;fn();return ()=>{};}};
  Object.assign(system,{
    world:{getSystem:c=>c===TurnSystem?{config:{inputProvider:{peek:()=>provider}}}:comfort,
      getSceneObject:id=>id==='arrival-panel' ? (level.arrival ? {} : undefined) : (level.arrival ? undefined : {requireElementById:()=>root}),getSceneEntity:()=>entity,
      activeLevel:level,},
    queries:{menus:{entities:[{getValue:()=>menuOpen}]}},camera:{quaternion},renderer,xrManager:xr,
  });
  system.init();
  const axes=()=>provider.getMoveAxis({x:0,y:0});
  return {system,elements,overlay,body,doc,win,media,comfort,fields,xr,renderer,quaternion,provider,nativeGet,axes,level};
}

test('arrival toolbar opens comfort and retains identity access, without a nonexistent estate panel',()=>{
 const h=setup();h.level.arrival=true;h.level.notify();
 assert.equal(h.elements.get('#mobile-estate').hidden,true);
 assert.equal(h.elements.get('#mobile-friends').textContent,'Accueil');
 h.elements.get('#mobile-comfort').emit('click');assert.equal(h.elements.get('#mobile-comfort').attrs['aria-expanded'],'true');
 h.elements.get('#mobile-friends').emit('click');assert.equal(h.body.classList.contains('mobile-friends-open'),true);
 assert.equal(h.elements.get('#mobile-comfort').attrs['aria-expanded'],'false');
 h.level.arrival=false;h.level.notify();assert.equal(h.elements.get('#mobile-estate').hidden,false);
 assert.equal(h.elements.get('#mobile-friends').textContent,'Amis');assert.equal(h.overlay.dataset.blocked,'false');
});

test('real pointer handlers allow simultaneous walking/looking and cancellation stops motion',()=>{
  const h=setup(),stick=h.elements.get('#mobile-stick'),look=h.elements.get('#mobile-look');
  stick.emit('pointerdown',{pointerId:1,clientX:50,clientY:18});
  assert.equal(h.axes().y,-1);
  look.emit('pointerdown',{pointerId:2,clientX:200,clientY:200});
  look.emit('pointermove',{pointerId:2,clientX:240,clientY:190});
  assert.ok(h.quaternion.y<0);assert.ok(h.quaternion.x>0);
  look.emit('pointerup',{pointerId:2});assert.equal(h.axes().y,-1);
  stick.emit('pointercancel',{pointerId:1});assert.equal(h.axes().y,0);
  assert.equal(stick.captures.size,0);
});

test('menus stop movement, opening another panel closes the previous one, blur releases touches',()=>{
  const h=setup(),stick=h.elements.get('#mobile-stick');
  stick.emit('pointerdown',{pointerId:1,clientX:50,clientY:18});
  h.elements.get('#mobile-comfort').emit('click');
  assert.equal(h.axes().y,0);assert.equal(h.overlay.dataset.blocked,'true');
  h.elements.get('#mobile-friends').emit('click');
  assert.equal(h.body.classList.contains('mobile-friends-open'),true);
  h.elements.get('#mobile-estate').emit('click');
  assert.equal(h.body.classList.contains('mobile-friends-open'),false);
  assert.equal(h.fields.display,'flex');
  h.elements.get('#mobile-estate').emit('click');
  stick.emit('pointerdown',{pointerId:3,clientX:50,clientY:18});
  h.win.emit('blur');assert.equal(h.axes().y,0);assert.equal(stick.captures.size,0);
});

test('resize/VR transitions reset gestures, hide touch UI, and cleanup restores native provider',()=>{
  const h=setup(),stick=h.elements.get('#mobile-stick');
  assert.equal(h.renderer.ratio,1.5);
  stick.emit('pointerdown',{pointerId:1,clientX:50,clientY:18});
  h.win.emit('resize');assert.equal(h.axes().y,0);
  h.xr.isPresenting=true;h.xr.emit('sessionstart');
  assert.equal(h.overlay.hidden,true);assert.equal(h.body.classList.contains('mobile-visit'),false);
  h.xr.isPresenting=false;h.xr.emit('sessionend');assert.equal(h.overlay.hidden,false);
  h.system.cleanupFuncs.forEach(fn=>fn());
  assert.equal(h.provider.getMoveAxis,h.nativeGet);assert.equal(h.overlay.removed,true);assert.equal(h.renderer.ratio,2);
});

test('headsets and touchscreen desktops never create virtual controls, even with touch=1',()=>{
  for (const userAgent of [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/126.0 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64; Quest 3) OculusBrowser/33.0.0 Chrome/126.0.6478.122 VR Safari/537.36',
    'Mozilla/5.0 (Linux; Android 12) Mobile OculusBrowser/33.0',
    'Mozilla/5.0 (Linux; Android 10; PICO 4) PicoBrowser/3.0 Mobile Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) Safari/605.1.15',
  ]) {
    const h=setup({userAgent,platform:'',maxTouchPoints:/Macintosh/.test(userAgent)?0:5});
    assert.equal(h.elements.size,0,userAgent);
    assert.equal(h.body.classList.contains('mobile-visit'),false);
    assert.equal(h.provider.getMoveAxis,h.nativeGet);
    assert.equal(h.renderer.ratio,2);
  }
});

test('phones and tablets including desktop-mode iPad retain virtual controls',()=>{
  for(const device of [
    {userAgent:'Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X)',platform:'iPhone',maxTouchPoints:5},
    {userAgent:'Mozilla/5.0 (iPad; CPU OS 18_0 like Mac OS X)',platform:'iPad',maxTouchPoints:5},
    {userAgent:'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15) Safari/605.1.15',platform:'MacIntel',maxTouchPoints:5},
    {userAgent:'Mozilla/5.0 (Linux; Android 14; Tablet) Chrome/126 Safari/537.36',platform:'Linux armv8l',maxTouchPoints:5},
  ]) {
    const h=setup(device);
    assert.equal(h.overlay.hidden,false,device.userAgent);
    assert.equal(h.body.classList.contains('mobile-visit'),true);
  }
});
