const assert=require('node:assert/strict'),vm=require('node:vm'),fs=require('node:fs'),path=require('node:path');
const ctx=vm.createContext({});
for(const file of ['data/courses.js','src/course-model.js'])vm.runInContext(fs.readFileSync(path.join(__dirname,'..',file),'utf8'),ctx);
const result=vm.runInContext(`courseSequences.map((s,r)=>({stages:courseStageCount(r),length:courseLength(r),start:courseBend(r,0),end:courseBend(r,courseLength(r)),last:courseStage(r,courseLength(r)),finite:Array.from({length:courseLength(r)},(_,n)=>courseBend(r,n)).every(Number.isFinite)}))`,ctx);
assert.deepEqual(Array.from(result,v=>v.stages),[6,10,14,18]);
assert.ok(result.every(v=>v.start===0&&v.end===0&&v.last===v.stages-1&&v.finite));
console.log('PASS: all four courses, endpoints, stage counts and finite curve samples');
