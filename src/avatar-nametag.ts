import { CanvasTexture, Sprite, SpriteMaterial, SRGBColorSpace, LinearFilter, Vector2 } from '@iwsdk/core';

const borders=new WeakMap<Sprite,{value:number}>();

/** Smooth the same three transmitted bands on every client, without repainting text. */
export function animateNameTagVoice(tag:Sprite,bands:ArrayLike<number>,delta:number,fresh=true):void {
  const border=borders.get(tag);if(!border)return;
  const energy=fresh?Math.min(1,.4*bands[0]+.4*bands[1]+.2*bands[2]):0;
  const target=3+16*energy;
  const alpha=1-Math.exp(-Math.max(0,delta)*(target>border.value?24:12));
  border.value+=(target-border.value)*alpha;
}

/** One texture per arrival, no text rasterization or allocation in update(). */
export function createNameTag(nickname:string):Sprite {
  const canvas = document.createElement('canvas');
  canvas.width = 1024; canvas.height = 128;
  const ctx = canvas.getContext('2d')!;
  ctx.font = '600 54px system-ui, sans-serif';
  const width = Math.min(1024,Math.ceil(ctx.measureText(nickname).width + 64));
  canvas.width = width;
  ctx.fillStyle = 'rgba(24,48,39,0.94)';
  ctx.beginPath();ctx.roundRect(0,0,width,128,24);ctx.fill();
  ctx.font = '600 54px system-ui, sans-serif';
  ctx.fillStyle = '#fff5df';ctx.textAlign = 'center';ctx.textBaseline = 'middle';
  ctx.fillText(nickname,width/2,64,width-48);
  const texture = new CanvasTexture(canvas); texture.colorSpace = SRGBColorSpace;
  texture.minFilter = LinearFilter; texture.generateMipmaps = false;
  const tag = new Sprite(new SpriteMaterial({map:texture,depthTest:true,depthWrite:false,toneMapped:false}));
  const border={value:3};borders.set(tag,border);
  tag.material.onBeforeCompile=shader=>{
    shader.uniforms.voiceBorder=border;shader.uniforms.tagSize={value:new Vector2(width,128)};
    shader.fragmentShader='uniform float voiceBorder;\nuniform vec2 tagSize;\n'+shader.fragmentShader;
    shader.fragmentShader=shader.fragmentShader.replace('#include <map_fragment>',`#include <map_fragment>
      vec2 tagPoint=abs(vMapUv*tagSize-tagSize*.5)-(tagSize*.5-vec2(24.));
      float edge=length(max(tagPoint,0.))+min(max(tagPoint.x,tagPoint.y),0.)-24.;
      float stroke=smoothstep(-voiceBorder-1.,-voiceBorder+1.,edge)*(1.-smoothstep(-1.5,0.,edge));
      diffuseColor.rgb=mix(diffuseColor.rgb,vec3(.706,.592,.349),stroke);
      diffuseColor.a=max(diffuseColor.a,stroke);
    `);
  };
  tag.material.customProgramCacheKey=()=> 'court-voice-border-v1';
  tag.name = `Pseudo : ${nickname}`;
  tag.scale.set(.24*width/128,.24,1);
  return tag;
}

export function disposeNameTag(tag:Sprite):void {
  borders.delete(tag);
  tag.material.map?.dispose(); tag.material.dispose();
}
