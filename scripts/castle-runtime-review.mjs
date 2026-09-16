import {readFileSync,writeFileSync} from 'node:fs';
const configPath='iwsdk.config.json', scenePath='public/scenes/plaisance.iwsdk.scene.json';
const backup='artifacts/castle-refinement/runtime-original.json';
if(process.argv[2]==='restore'){
  const original=JSON.parse(readFileSync(backup));
  writeFileSync(scenePath,original.scene);writeFileSync(configPath,original.config);
}else{
  const original={config:readFileSync(configPath,'utf8'),scene:readFileSync(scenePath,'utf8')};
  writeFileSync(backup,JSON.stringify(original));
  const scene=JSON.parse(original.scene),config=JSON.parse(original.config);
  const hero=scene.authoring.views.find(v=>v.id==='hero');
  hero.position=[6.2,6.8,-24.2];hero.target=[10.1,6.05,-30.9];hero.fov=75;
  writeFileSync(scenePath,JSON.stringify(scene,null,2)+'\n');
  config.scene='./public/scenes/plaisance.iwsdk.scene.json';
  writeFileSync(configPath,JSON.stringify(config,null,2)+'\n');
}
