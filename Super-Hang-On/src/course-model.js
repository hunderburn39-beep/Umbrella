'use strict';
// ROM records: position, radius, turn type. Verified against 49,152 sub-CPU vectors.
// Browser visual scaling and transition smoothing are still approximations.
const BLOCK_UNITS=2048,STAGE_UNITS=1024;
function courseLength(route){return courseSequences[route].length*BLOCK_UNITS}
function courseStageCount(route){return 2*courseSequences[route].length}
function courseStage(route,z){return Math.min(courseStageCount(route)-1,Math.max(0,Math.floor(z/STAGE_UNITS)))}
function turnValue(r){return r[2]===1?0:(r[2]===2?1:-1)*Math.min(2,64/r[1])}
function courseBend(route,z){
 if(z<=0||z>=courseLength(route))return 0;
 const seq=courseSequences[route],id=seq[Math.floor(z/BLOCK_UNITS)],local=z%BLOCK_UNITS,rows=courseBlocks[id];
 let lo=0,hi=rows.length-1;
 while(lo<hi){const mid=Math.ceil((lo+hi)/2);if(rows[mid][0]<=local)lo=mid;else hi=mid-1}
 const cur=rows[lo],prev=lo?rows[lo-1]:cur,next=rows[lo+1];
 const t=Math.min(1,(local-cur[0])/Math.min(6,next?next[0]-cur[0]:6));
 const smooth=t*t*(3-2*t);
 return turnValue(prev)+(turnValue(cur)-turnValue(prev))*smooth;
}
if(typeof module!=='undefined'&&module.exports)module.exports={courseLength,courseStageCount,courseStage,courseBend,turnValue};
