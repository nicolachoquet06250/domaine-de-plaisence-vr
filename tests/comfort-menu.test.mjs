import { readFileSync } from 'node:fs';
import vm from 'node:vm';
import assert from 'node:assert/strict';
import { test } from 'node:test';
import ts from 'typescript';

// Exercise the real system's event handlers and lifecycle without a renderer.
// Rendering, controller input and ray clicks are separately checked in IWSDK.
const compiled = ts.transpileModule(readFileSync(new URL('../src/comfort-menu.ts', import.meta.url), 'utf8'), {
  compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022 },
}).outputText;

async function setup(saved = null, storageAvailable = true) {
  const listeners = new Map();
  class HTMLElement { tagName = 'DIV'; isContentEditable = false; }
  class Vector3 {
    x = 0; y = 0; z = 0;
    set(x,y,z) { Object.assign(this,{x,y,z}); return this; }
    copy(v) { return this.set(v.x,v.y,v.z); }
    applyQuaternion() { return this; }
    addScaledVector(v,s) { this.x+=v.x*s; this.y+=v.y*s; this.z+=v.z*s; return this; }
  }
  class Quaternion { copy() { return this; } identity() { return this; } }
  const Settings = {}, ScreenSpace = {}, RayInteractable = {};
  const components = new Map();
  const elements = new Map();
  const document = {
    parent: null, position: new Vector3(), quaternion: new Quaternion(), clears: 0,
    clearTargetDimensions() { this.clears++; },
  };
  const panel = {
    document, position: new Vector3(), quaternion: new Quaternion(), disposed: false,
    add(child) { child.parent = this; }, dispose() { this.disposed = true; },
    requireElementById(id) {
      if (!elements.has(id)) elements.set(id, {
        props: {}, events: new Map(),
        setProperties(value) { Object.assign(this.props,value); },
        addEventListener(name,handler) { this.events.set(name,handler); },
        removeEventListener(name) { this.events.delete(name); },
      });
      return elements.get(id);
    },
  };
  panel.add(document);
  const entity = {
    addComponent(c,value={}) { components.set(c,value); return this; },
    removeComponent(c) { components.delete(c); }, hasComponent(c) { return components.has(c); },
    setValue(c,key,value) { components.get(c)[key]=value; }, dispose() { panel.dispose(); },
  };
  const signal = { value: .5, peek() { return this.value; } };
  const voice = {micClicks:0,listenClicks:0,unsubscribed:false,notify:null,inLobby:false,enters:0,leaves:0,
    toggleMicrophone(){this.micClicks++;},toggleVoiceListening(){this.listenClicks++;},
    subscribeVoice(fn){this.notify=fn;fn({microphone:'off',listening:false,connectedPeers:0,error:''});return ()=>{this.unsubscribed=true;};}};
  const visibility = { current: 'browser', peek() { return this.current; }, subscribe(fn) { this.notify=fn; return () => {}; } };
  const level = { arrival: false, subscribe(fn) { this.notify=fn; fn(); return () => {}; } };
  const exports = {};
  const core = {
    createSystem: () => class { cleanupFuncs = []; },
    InputComponent: { B_Button: 'B' }, LocomotionSystem: class {}, ScreenSpace, RayInteractable,
    Vector3, Quaternion, VisibilityState: { NonImmersive: 'browser' },
  };
  vm.runInNewContext(compiled, {
    exports, require: name => name === '@iwsdk/core' ? core : { ComfortSettings: Settings },
    HTMLElement, console, document: { body: { classList: { contains: () => false } } },
    window: { addEventListener: (name,fn) => listeners.set(name,fn), removeEventListener: name => listeners.delete(name) },
    localStorage: {
      getItem() { if (!storageAvailable) throw Error('disabled'); return saved; },
      setItem(_key,value) { if (!storageAvailable) throw Error('disabled'); saved=value; },
    },
  });
  const system = new exports.ComfortMenuSystem();
  const camera = {
    getWorldPosition(v) { v.set(0,1.65,24); }, getWorldQuaternion() {},
  };
  Object.assign(system, {
    world: { getSystem: () => ({ config: { comfortAssist: signal },isInLobby:()=>voice.inLobby,getEntryLabel:()=>voice.pendingInvitation?'Accéder à la room':'Créer un salon et entrer',enterLobby:()=>voice.enters++,leaveLobby:()=>voice.leaves++,toggleMicrophone:()=>voice.toggleMicrophone(),toggleVoiceListening:()=>voice.toggleVoiceListening(),subscribeVoice:fn=>voice.subscribeVoice(fn) }), visibilityState: visibility,
      activeLevel: level, getSceneObject: () => level.arrival ? panel : undefined,
      assets: { instantiate: async () => panel }, createTransformEntity: () => entity },
    visibilityState: visibility, camera, xrManager: { isPresenting: false },
  });
  system.init();
  await Promise.resolve();
  function key(code,extra={}) {
    const event={ code, target: null, preventDefault() { this.prevented=true; }, ...extra };
    listeners.get('keydown')?.(event);
    return event;
  }
  return { system, key, signal, panel, document, camera, visibility, components, ScreenSpace, RayInteractable,
    settings: () => components.get(Settings), saved: () => saved, HTMLElement, elements, listeners, voice, level };
}

test('arrival exposes only comfort with M and B, preserves settings and closes on scene transitions',async()=>{
 const h=await setup();h.level.arrival=true;h.level.notify();h.key('KeyM');
 assert.equal(h.settings().open,true);
 for(const id of ['comfort-session','comfort-voice'])assert.equal(h.elements.get(id).props.display,'none');
 for(const id of ['comfort-session','comfort-microphone','comfort-listening'])h.elements.get(id).events.get('click')();
 assert.equal(h.voice.enters+h.voice.micClicks+h.voice.listenClicks,0);
 h.key('Digit3');assert.equal(h.signal.value,.75);
 h.level.arrival=false;h.level.notify();assert.equal(h.settings().open,false);
 assert.equal(h.elements.get('comfort-session').props.display,'flex');
 h.level.arrival=true;h.level.notify();h.visibility.current='vr';h.system.xrManager.isPresenting=true;
 let down=true;h.system.input={xr:{gamepads:{right:{getButtonDown(button){assert.equal(button,'B');const value=down;down=false;return value;}}}}};
 h.system.update();assert.equal(h.settings().open,true);assert.equal(h.components.has(h.ScreenSpace),false);
 h.system.update();assert.equal(h.settings().open,true,'held B does not flicker');
 down=true;h.system.update();assert.equal(h.settings().open,false);assert.equal(h.signal.value,.75);
});

test('voice buttons use the multiplayer service only while open and mirror voice status',async()=>{
  const h=await setup();const mic=h.elements.get('comfort-microphone');const listen=h.elements.get('comfort-listening');
  mic.events.get('click')();listen.events.get('click')();assert.equal(h.voice.micClicks,0);assert.equal(h.voice.listenClicks,0);
  h.key('KeyM');mic.events.get('click')();listen.events.get('click')();assert.equal(h.voice.micClicks,1);assert.equal(h.voice.listenClicks,1);
  h.voice.notify({microphone:'on',listening:true,listeningPaused:false,connectedPeers:1,error:''});
  assert.equal(mic.props.text,'Couper le micro');assert.equal(listen.props.text,"Couper l'ecoute");
  h.voice.notify({microphone:'off',listening:true,listeningPaused:true,connectedPeers:1,error:'Lecture bloquée'});
  assert.equal(listen.props.text,"Reprendre l'ecoute");assert.equal(h.elements.get('comfort-voice-status').props.text,'Lecture bloquee');
  h.system.cleanupFuncs.forEach(fn=>fn());assert.equal(h.voice.unsubscribed,true);assert.equal(mic.events.size,0);assert.equal(listen.events.size,0);
});

test('session menu creates a room in solo and disconnects from the lobby',async()=>{
  const h=await setup();const button=h.elements.get('comfort-session');
  assert.equal(button.props.text,'Creer un salon et entrer');
  assert.equal(h.elements.get('comfort-voice').props.display,'none');
  h.voice.pendingInvitation=true;h.voice.notify({microphone:'off',listening:false,connectedPeers:0,error:''});
  assert.equal(button.props.text,'Acceder a la room');
  h.key('KeyM');button.events.get('click')();assert.equal(h.voice.enters,1);assert.equal(h.settings().open,false);
  h.voice.inLobby=true;h.voice.notify({microphone:'off',listening:false,connectedPeers:1,error:''});
  assert.equal(button.props.text,'Se deconnecter');assert.equal(h.elements.get('comfort-voice').props.display,'flex');
  h.key('KeyM');button.events.get('click')();assert.equal(h.voice.leaves,1);assert.equal(h.settings().open,false);
  button.events.get('click')();assert.equal(h.voice.leaves,1,'closed menu cannot disconnect twice');
});

test('M opens/closes, 0-4 selects levels, Escape closes and handlers clean up', async () => {
  const h = await setup();
  assert.equal(h.panel.visible,false);
  assert.equal(h.key('KeyM').prevented,true);
  assert.equal(h.settings().open,true);
  assert.equal(h.components.has(h.ScreenSpace),true);
  for (let i=0;i<5;i++) {
    h.key(`Digit${i}`);
    assert.equal(h.signal.value,i/4);
    assert.equal(h.saved(),JSON.stringify(i/4));
  }
  h.key('Escape');
  assert.equal(h.panel.visible,false);
  assert.equal(h.components.has(h.RayInteractable),false);
  h.key('Digit0');
  assert.equal(h.signal.value,1);
  h.key('KeyM'); h.key('KeyM');
  assert.equal(h.settings().open,false);
  h.system.cleanupFuncs.forEach(fn=>fn());
  assert.equal(h.listeners.has('keydown'),false);
  assert.equal(h.panel.disposed,true);
});

test('held keys, modifiers and text fields do not toggle the menu', async () => {
  const h = await setup();
  const input = new h.HTMLElement(); input.tagName='INPUT';
  const editable = new h.HTMLElement(); editable.isContentEditable=true;
  for (const extra of [{repeat:true},{ctrlKey:true},{metaKey:true},{altKey:true},{target:input},{target:editable}]) {
    h.key('KeyM',extra);
    assert.equal(h.panel.visible,false);
  }
});

test('browser close restores the document before opening it in VR', async () => {
  const h = await setup();
  h.key('KeyM');
  // Model the documented ScreenSpace reparenting performed by the SDK.
  h.document.parent=h.camera;
  h.document.position.set(1,2,-.2);
  h.visibility.current='vr'; h.visibility.notify();
  assert.equal(h.document.parent,h.panel);
  assert.equal(h.document.position.z,0);
  assert.equal(h.document.clears,1);
  h.key('KeyM');
  assert.equal(h.components.has(h.ScreenSpace),false);
  assert.equal(h.panel.position.z,22.75);
  assert.equal(h.panel.visible,true);
});

test('saved setting restores; corrupt or unavailable storage remains usable', async () => {
  const restored = await setup('0.75');
  assert.equal(restored.signal.value,.75);
  for (const raw of ['null','-1','2','{}','broken']) assert.equal((await setup(raw)).signal.value,.5);
  const disabled = await setup(null,false);
  disabled.key('KeyM'); disabled.key('Digit0');
  assert.equal(disabled.signal.value,0);
  assert.equal(disabled.elements.get('comfort-saved').props.text,'Choix actif pour cette visite.');
});
