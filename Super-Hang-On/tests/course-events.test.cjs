const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm'),path=require('node:path');
const ctx=vm.createContext({});
for(const f of ['data/courses.js','src/course-model.js','data/course-events.js','src/course-events.js'])vm.runInContext(fs.readFileSync(path.join(__dirname,'..',f),'utf8'),ctx);
assert.equal(vm.runInContext('heightEvents.flat().length',ctx),103);
assert.equal(vm.runInContext('objectEvents.flat().length',ctx),1283);
assert.equal(vm.runInContext('objectEvents[13].some((v,i,a)=>i>0&&v[0]<a[i-1][0])',ctx),true);
assert.equal(vm.runInContext('courseSequences.every((s,r)=>Array.from({length:s.length*8},(_,i)=>visibleCourseObjects(r,i*256).every(o=>o.d>5&&o.d<=1800)).every(Boolean))',ctx),true);
assert.equal(vm.runInContext('courseSequences.every((s,r)=>Number.isInteger(currentHeightProfile(r,0)))',ctx),true);
console.log('PASS: record counts, ordering and visibility across all four routes');
