'use strict';
// Selective ROM US translation, not a CPU emulator.
function lookupIndex(word0,word4){
 const d=((((word0&65535)<<16)|(word4&65535))-0x10001010)>>>0;
 return ((((((d&65535)>>>3)<<5)+((d>>>16)>>>4))&65535)<<16)>>16;
}
function replaceHigh(v,w){return ((w&65535)<<16)|(v&65535)}
function integrationSubstep(positions,velocities){
 if(positions.length!==6||velocities.length!==6)throw RangeError('Expected six longwords each');
 let signMask=0;
 const absolute=velocities.map((v,i)=>{v|=0;if(v<0){signMask|=1<<i;return (-v)|0}return v});
 const increment=velocities.map(v=>(v|0)>>3);
 return {positions:positions.map((p,i)=>(p+increment[i])|0),absolute,signMask,increment};
}
function initialPosition(old=[0,0]){return [replaceHigh(old[0],0x11f4),replaceHigh(old[1],0x102c)]}
function launchVelocity(index,old,d){return (replaceHigh(old,-d.launch_table[index&255])+d.acceleration)|0}
function response(positions,velocity,map,d,aux=false){
 const index=lookupIndex(positions[0]>>>16,positions[1]>>>16),cells=aux?d.special:d.maps[map].cells;
 if(index<0||index>=cells.length)return {supported:false,index};
 const code=cells[index],pair=d.impulses[code&63];
 return {supported:true,index,code,flags:(code&192)>>>2,velocity:[(velocity[0]+pair[1])|0,(velocity[1]+pair[0])|0]};
}
function state0(positions,velocity,map,d){
 if(map===2)return response(positions,velocity,map,d,true);
 return {supported:true,velocity:[(velocity[0]+d.acceleration)|0,velocity[1]|0]};
}
function toScreen(p){return [224-(p[1]/65536-0x1010),p[0]/65536-0x1000]}
function traceFreeFrame(positions,velocities,d){
 const trace=[];for(let i=0;i<d.substeps;i++){let r=integrationSubstep(positions,velocities);positions=r.positions;trace.push(r)}return trace;
}
if(typeof module!=='undefined')module.exports={lookupIndex,replaceHigh,integrationSubstep,initialPosition,launchVelocity,response,state0,toScreen,traceFreeFrame};
