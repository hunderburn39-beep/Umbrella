const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm'),path=require('node:path');
const ctx=vm.createContext({});
for(const f of ['data/courses.js','src/course-model.js','data/course-events.js','data/height-profiles.js','src/height-model.js'])vm.runInContext(fs.readFileSync(path.join(__dirname,'..',f),'utf8'),ctx);
assert.equal(vm.runInContext('heightProfileSamples.reduce((a,b)=>a+b[0],0)',ctx),7700);
assert.ok(vm.runInContext('heightProfileSamples.every(([n,a])=>a.length===Math.ceil(n/16)+1)',ctx));
assert.ok(vm.runInContext('courseSequences.every((s,r)=>Array.from({length:courseLength(r)},(_,i)=>courseHill(r,i)).every(v=>Number.isFinite(v)&&Math.abs(v)<=45))',ctx));
assert.ok(vm.runInContext('heightTimeline.every(events=>events.every(([z,id])=>id>=1&&id<=21))',ctx));
console.log('PASS: profiles and all four route timelines');
