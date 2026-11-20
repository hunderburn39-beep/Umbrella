'use strict';
// Direct translation of geometry predicates only (US ROM). No fabricated bounce.
const w16=v=>v&65535, sw16=v=>(v<<16)>>16;
function narrowSurface(record,x,y){
 if(!Array.isArray(record)||record.length!==8||!Number.isInteger(x)||!Number.isInteger(y)||x<0||x>=512||y<16||y>=240)throw RangeError('record/visible coordinate');
 const [flags,lo,hi,a,b,c,angle,event]=record,t=flags&15;
 const base={type:t,event,flags,angle};
 if(t===2||t===3)return {...base,status:'pending',reason:'curved handler not ported'};
 if(t===8){const hit=y>=lo&&y<=hi&&x>=a&&x<=b;return {...base,status:hit?'zone':'miss',bounds:[a,lo,b,hi],target:[c,angle]};}
 if(t>8)return {...base,status:'pending'};
 const across=t===4||t===5?x:y;
 if(across<lo||across>hi)return {...base,status:'miss',reason:'range'};
 let target,coordinate,limit;
 if(t<2){
   const numerator=sw16(a)*sw16(y),denominator=sw16(b);
   if(!denominator)return {...base,status:'pending',reason:'divide by zero'};
   const q=Math.trunc(numerator/denominator);if(q< -32768||q>32767)return {...base,status:'pending',reason:'DIVS overflow'};
   target=w16((q+sw16(c))*2);coordinate=x;limit=15;
 }else{target=a;coordinate=t<6?y:x;limit=8;}
 const delta=sw16(coordinate-target),signMismatch=delta!==0&&((coordinate<target?1:0)!==(t&1));
 return {...base,status:!signMismatch&&Math.abs(delta)<limit?'contact':'miss',delta,target,axis:t<2||t>=6?'x':'y',limit,reason:signMismatch?'side':Math.abs(delta)>=limit?'distance':'geometry'};
}
if(typeof module!=='undefined')module.exports={narrowSurface};
