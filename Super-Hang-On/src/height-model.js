'use strict';
// Timing and horizon gain remain provisional. Position units follow the current browser course.
const heightTimeline=courseSequences.map(seq=>seq.flatMap((id,i)=>heightEvents[id].map(([pos,profile])=>[i*BLOCK_UNITS+pos,profile])).sort((a,b)=>a[0]-b[0]));
function slopeAt(route,z){
 const events=heightTimeline[route];
 let lo=-1,hi=events.length-1;
 while(lo<hi){const m=Math.ceil((lo+hi)/2);if(events[m][0]<=z)lo=m;else hi=m-1}
 if(lo<0)return 0;
 const [start,id]=events[lo],[length,samples]=heightProfileSamples[id-1],pos=z-start;
 if(pos<0||pos>=length)return 0;
 const i=Math.floor(pos/16),t=pos/16-i;
 return Math.max(-1,Math.min(1,(samples[i]+(samples[i+1]-samples[i])*t)/4096));
}
function courseHill(route,z){return 45*slopeAt(route,z);}
