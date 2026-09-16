import { mkdir, writeFile } from 'node:fs/promises';
const revision='d3af5f9ff86ab6b2b1913d411a4e1922ec101953';
const base=`https://raw.githubusercontent.com/met4citizen/HeadAudio/${revision}/`;
await mkdir('public/vendor/headaudio',{recursive:true});
for(const [source,destination] of [
  ['dist/headworklet.min.mjs','public/vendor/headaudio/headworklet.mjs'],
  ['dist/model-en-mixed.bin','public/vendor/headaudio/model-en-mixed.bin'],
  ['LICENSE','public/vendor/headaudio/LICENSE'],
  ['modules/training.mjs','artifacts/avatars/headaudio-training-source.mjs'],
  ['modules/processor.mjs','artifacts/avatars/headaudio-processor-source.mjs'],
]) {
  const r=await fetch(base+source);if(!r.ok)throw Error(`${source}: ${r.status}`);
  const data=new Uint8Array(await r.arrayBuffer());await writeFile(destination,data);console.log(destination,data.length);
}
