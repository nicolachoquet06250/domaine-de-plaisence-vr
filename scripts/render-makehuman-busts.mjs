import {execFileSync} from 'node:child_process';
import {writeFile,mkdir} from 'node:fs/promises';
const out='artifacts/busts-makehuman/validation';await mkdir(out,{recursive:true});
const jobs=[
 ...['francois','louis','catherine','anne'].map(n=>({path:'public/scenes/visit.iwsdk.scene.json',viewId:'bust-'+n,name:'castle-'+n})),
 ...['francois','louis','catherine','anne'].map(n=>({path:'public/scenes/busts-makehuman-review.iwsdk.scene.json',viewId:'royal-'+n+'-profile',name:'profile-'+n})),
 {path:'public/scenes/plaisance.iwsdk.scene.json',viewId:'bust-anne',name:'plaisance-anne'},
 {path:'public/scenes/visit.iwsdk.scene.json',viewId:'hero',name:'visit-spawn'},
];
const report=[];
for(const job of jobs){
 const text=execFileSync(process.execPath,['node_modules/@iwsdk/cli/bin/iwsdk.js','scene','render-file','--input-json',JSON.stringify({path:job.path,viewId:job.viewId,width:740,height:820}),'--output-file',`${out}/${job.name}.png`],{encoding:'utf8',timeout:60000,maxBuffer:5*1024*1024});
 const r=JSON.parse(text);report.push({job,...r});await writeFile(`${out}/renders.json`,JSON.stringify(report,null,2));console.log(job.name,r.ok);
 if(!r.ok)throw new Error(text);
}
