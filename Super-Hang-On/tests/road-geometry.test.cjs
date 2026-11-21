const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const {buildRoadGeometry,sampleRoad}=require('../src/road-geometry.js');
const rows=JSON.parse(fs.readFileSync(path.join(__dirname,'../data/road.js'),'utf8').match(/const roadROM=(\[[\s\S]*?\]);/)[1]);
const shapes=buildRoadGeometry(rows);
assert.equal(shapes.length,191);
assert.equal(sampleRoad(shapes,0),shapes[0]);
assert.equal(sampleRoad(shapes,1),shapes[190]);
for(const q of shapes){
  assert.ok(q.half>0);
  assert.ok(Math.abs((q.right-q.mid)*q.scale-q.half)<1e-9);
  assert.ok(Math.abs((q.left-q.mid)*q.scale+q.half)<1e-9);
}
console.log('PASS: all 191 road projections align with their decoded road boundaries');
