import { AdditiveBlending, BufferGeometry, DoubleSide, Float32BufferAttribute, Mesh, ShaderMaterial } from '@iwsdk/core';

// Crossed sheets retain volume from oblique views and in stereo: 32 triangles,
// one draw call per hearth, no simulation, texture downloads or particle churn.
const position: number[] = [], uv: number[] = [], seed: number[] = [], indices: number[] = [];
for (let i = 0; i < 8; i++) {
  const x = -.48 + (i % 4) * .30, z = i < 4 ? .025 : .24;
  const height = .52 + .19 * (.5 + .5 * Math.sin(i * 5.1));
  for (const angle of [0, Math.PI / 2]) {
    const base = position.length / 3;
    for (const [u, v] of [[0, 0], [1, 0], [0, 1], [1, 1]]) {
      const width = (u - .5) * .37;
      position.push(x + Math.cos(angle) * width, .17 + v * height, z + Math.sin(angle) * width);
      uv.push(u, v); seed.push(i * 2.31);
    }
    indices.push(base, base + 1, base + 2, base + 2, base + 1, base + 3);
  }
}
const geometry = new BufferGeometry();
geometry.setAttribute('position', new Float32BufferAttribute(position, 3));
geometry.setAttribute('uv', new Float32BufferAttribute(uv, 2));
geometry.setAttribute('flameSeed', new Float32BufferAttribute(seed, 1));
geometry.setIndex(indices); geometry.computeBoundingBox(); geometry.computeBoundingSphere();
const material = new ShaderMaterial({
  name: 'Flammes turbulentes', transparent: true, depthWrite: false,
  side: DoubleSide, blending: AdditiveBlending, uniforms: { time: { value: 1.7 } },
  vertexShader: `
    attribute float flameSeed;
    varying vec2 vUv; varying float vSeed;
    void main() { vUv = uv; vSeed = flameSeed; gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }
  `,
  fragmentShader: `
    uniform float time;
    varying vec2 vUv; varying float vSeed;
    float hash(vec2 p) { return fract(sin(dot(p,vec2(127.1,311.7))) * 43758.5453); }
    float noise(vec2 p) {
      vec2 i=floor(p), f=fract(p); f=f*f*(3.0-2.0*f);
      return mix(mix(hash(i),hash(i+vec2(1,0)),f.x),mix(hash(i+vec2(0,1)),hash(i+vec2(1,1)),f.x),f.y);
    }
    void main() {
      float t=time*1.65+vSeed;
      vec2 p=vec2(vUv.x-.5,vUv.y);
      float n=noise(vec2(p.x*5.0+vSeed,p.y*4.0-t));
      float detail=noise(vec2(p.x*13.0-vSeed,p.y*9.0-t*1.7));
      float sway=sin(p.y*7.0-t*1.8)*.10*p.y+(n-.5)*.22*p.y;
      float taper=.43*pow(max(0.0,1.0-p.y),.85);
      float density=taper-abs(p.x+sway)+(n-.5)*.17+(detail-.5)*.055;
      float alpha=smoothstep(-.035,.065,density)*smoothstep(0.0,.10,p.y)*(1.0-smoothstep(.73,1.0,p.y));
      if(alpha<.012) discard;
      float core=smoothstep(.035,.30,density)*(1.0-p.y);
      vec3 color=mix(vec3(1.9,.19,.009),vec3(3.0,2.0,.65),core);
      gl_FragColor=vec4(color,alpha*.68);
      #include <tonemapping_fragment>
      #include <colorspace_fragment>
    }
  `,
});
export const hearthFire = new Mesh(geometry, material);
hearthFire.name = 'Flammes au-dessus des buches';
hearthFire.renderOrder = 2;
