'use strict';
// The EPR-10642.47 ROM has two 1-bit planes, 256 rows × 512 pixels.
// Rows 0–190 are the road taper; later rows include solid/background patterns.
function buildRoadGeometry(rows,scale=1.12){
  if(rows.length!==256)throw Error('Expected 256 road rows');
  return rows.slice(0,191).map((row,i)=>{
    let next=0;
    for(const [x,n,pen] of row){if(x!==next||n<1||pen<0||pen>3)throw Error('Invalid run '+i);next+=n}
    if(next!==512)throw Error('Invalid row width '+i);
    const first=row[0],last=row[row.length-1];
    const left=first[2]===3?first[1]:0;
    const right=last[2]===3?last[0]:512;
    if(right<=left)throw Error('Invalid road bounds '+i);
    return {row,left,right,mid:(left+right)/2,half:(right-left)*scale/2,scale};
  });
}
function sampleRoad(geometry,p){return geometry[Math.min(190,Math.max(0,Math.round(p*190)))];}
if(typeof module!=='undefined'&&module.exports)module.exports={buildRoadGeometry,sampleRoad};
