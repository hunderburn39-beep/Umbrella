'use strict';
// 136a–14d4: input-to-accumulator path, RAM speed supplied by caller.
function advanceFlippers(state,input,upStep,downStep,lock=false){
 if((state.flags>>>0)===0xffffffff)return {...state};
 for(const v of [state.a,state.b])if(!Number.isInteger(v)||v<0||v>0x6ffff)throw RangeError('Accumulator');
 for(const v of [upStep,downStep])if(!Number.isInteger(v)||v<0||v>65535)throw RangeError('RAM speed word');
 const mask=lock?0:input&3;let flags=(state.flags&0xbfffbfff)>>>0;
 function move(p,pressed,limitBit,directionBit){
  let n=pressed?p+upStep:p-downStep;
  if(pressed?n>=0x6ffff:n<0)flags=(flags|limitBit)>>>0;
  flags=(pressed?(flags|directionBit):(flags&~directionBit))>>>0;
  return Math.max(0,Math.min(0x6ffff,n));
 }
 const a=move(state.a,mask&1,0x40000000,0x80000000),b=move(state.b,mask&2,0x4000,0x8000);
 return {a,b,flags};
}
// 124c–12d4: two intermediate descriptors per selector; normal pass.
function descriptors(data,map,a,b){
 let angles=[a>>>16,b>>>16],attribute=0x14;
 return data.maps[map].flatMap(sel=>{const row=data.rows[sel-1],frame=angles[row.channel];if(frame>6)throw RangeError('Frame');if(sel>=5)attribute|=0x20;
 const tile=row.frames[frame];return [0,1].map(half=>({selector:sel,frame,attribute,tile:tile+16*half,colourSize:0x12,x:row.x+32*half,y:row.y}));});
}
// 63e–6ba: geometric separation only; no velocity exchange.
function separatePair(a,b,table,flags=0){
 const u=x=>x>>>0;let f=u(flags),dx=u(a[0]-b[0]),dy=u(a[1]-b[1]);
 if(u(a[0])<=u(b[0])){dx=u(-dx);f=u(f|64)}
 if(u(a[1])<u(b[1])){dy=u(-dy);f=u(f|128)}
 dy=u(dy*2);if(dx>=dy){[dx,dy]=[dy,dx];f=u(f|256)}
 const index=dx>>>16,miss=()=>({hit:false,a:[...a],b:[...b],index,flags:u((f&0xffff0000)|(f&63))});
 if(index>=21||table[index]<dy)return miss();
 let delta=table[index]-dy,p=[...a],q=[...b],axis=f&256?0:1;
 delta=delta>>>(axis===0?1:2);if(!(f&(axis===0?64:128)))delta=-delta;
 p[axis]=(p[axis]-delta)|0;q[axis]=(q[axis]+delta)|0;
 return {hit:true,a:p,b:q,index,axis,delta,flags:f};
}
if(typeof module!=='undefined')module.exports={advanceFlippers,descriptors,separatePair};
