'use strict';
// Raw event placement verified. A graphic assignment or object count per event is NOT decoded.
// The current renderer uses one illustrative atlas sprite per event, not original pattern expansion.
const sortedObjectEvents=objectEvents.map(rows=>rows.slice().sort((a,b)=>a[0]-b[0]));
function visibleCourseObjects(route,z,far=1800){
 const seq=courseSequences[route],out=[];
 const end=Math.min(seq.length-1,Math.floor((z+far)/BLOCK_UNITS));
 for(let b=Math.max(0,Math.floor(z/BLOCK_UNITS));b<=end;b++){
  for(const [local,code] of sortedObjectEvents[seq[b]]){
   const d=b*BLOCK_UNITS+local-z;
   if(d>5&&d<=far)out.push({d,code,block:seq[b],local});
  }
 }
 return out;
}
// Expose raw height-profile IDs for further decoding, do not invent their shape.
function currentHeightProfile(route,z){
 const seq=courseSequences[route],block=Math.max(0,Math.min(seq.length-1,Math.floor(z/BLOCK_UNITS)));
 const local=z-block*BLOCK_UNITS;
 let profile=1;
 for(const [at,id] of heightEvents[seq[block]]){if(at>local)break;profile=id}
 return profile;
}
