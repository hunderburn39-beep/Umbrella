'use strict';
// Isolated US ROM 0x63a–0x7aa translation, no CPU interpreter.
const u32=v=>v>>>0, i32=v=>v|0;
function mulHigh(a,b){
 const a0=a&65535,a1=a>>>16,b0=b&65535,b1=b>>>16;
 const mid=a0*b1+a1*b0+Math.floor(a0*b0/65536);
 return u32(a1*b1+Math.floor(mid/65536));
}
function velocityTransfer(index,flags,currentA,currentB,tables,originalA=currentA,originalB=currentB){
 if(!Number.isInteger(index)||index<0||index>=21)throw RangeError('contact index');
 const c=tables.coefficient_c[index],b=(flags&256?tables.coefficient_b:tables.coefficient_a)[index],neg=u32(-(b||1));
 function project(v){
 const x=u32(Math.abs(v[0]|0)),y=u32(Math.abs(v[1]|0));let t=[mulHigh(x,b),mulHigh(x,c),mulHigh(u32(y*2),neg),mulHigh(u32(y*2),c)].map(i32);
 if(v[0]<0){t[0]=i32(-t[0]);t[1]=i32(-t[1]);}if(v[1]<0){t[2]=i32(-t[2]);t[3]=i32(-t[3]);}
 if((flags&192)!==0&&(flags&192)!==192){t[1]=i32(-t[1]);t[3]=i32(-t[3]);}
 return [i32(t[0]+t[3]),i32(t[1]+t[2])>>1];
 }
 const pa=project(originalA),pb=project(originalB);
 return {a:currentA.map((v,j)=>i32(v-pa[j]+pb[j])),b:currentB.map((v,j)=>i32(v-pb[j]+pa[j])),projectionA:pa,projectionB:pb};
}
// Isolated contact with fresh flags, not the complete three-ball loop.
function contactPair(a,b,va,vb,tables){const r=separatePair(a,b,tables.distance);return r.hit?{...r,velocity:velocityTransfer(r.index,r.flags,va,vb,tables)}:{...r,velocity:{a:[...va],b:[...vb]}};}
// 0x82f6–0x83fa: visible-grid candidate lookup only.
function surfaceCandidates(d,map,difficulty,alternate,rawX,rawY,frameA,frameB){
 if(!Number.isInteger(rawX)||!Number.isInteger(rawY)||rawX<0||rawX>=512||rawY<16||rawY>=240)return null;
 const m=d.surfaces[difficulty][map][alternate?1:0],index=((rawY-16)>>3)*32+(rawX>>4),selector=m.cells[index];
 const words=selector?m.lists[selector-1]:[];
 return {index,selector,records:words.map(word=>{if(!(word&32768))return {word,address:m.geometry+(word-1)*16,dynamic:false};const channel=word&0x4000?1:0,frame=channel?frameB:frameA;if(!Number.isInteger(frame)||frame<0||frame>6)throw RangeError('frame');const base=d.dynamicBases[(word>>>8)&15],address=base+(word&15)*128+frame*16;return {word,address,dynamic:true,channel,frame};})};
}
function ballDescriptor(status,positions,pass){if(pass&~4)return null;let attr=pass===0?0x14:0x54;if(status<0)attr|=0x20;if((status<<16)>=0)attr&=~4;return {attribute:attr,tile:0x50+((status>>>16)&0x30),colourSize:2,x:(positions[0]>>>16)-0x1010,y:(positions[1]>>>16)-0x1008};}
if(typeof module!=='undefined'){globalThis.separatePair=require('../Fase8/flippers').separatePair;module.exports={mulHigh,velocityTransfer,contactPair,surfaceCandidates,ballDescriptor};}
