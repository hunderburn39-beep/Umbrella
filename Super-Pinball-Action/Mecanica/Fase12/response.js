'use strict';
// Selective US ROM translation. Fixed-point position in native screen pixels,
// before ROT90; longword velocity components use native x/y axes.
const wordSigned=w=>(w<<16)>>16;
function straight12(r,x,y){
 const [flags,lo,hi,a,b,c,angle,event]=r,t=flags&15,hx=x>>>1;
 const base={type:t,event,flags,angle};
 if(t===8)return {...base,status:y>=lo&&y<=hi&&hx>=a&&hx<=b?'zone':'miss',target:[angle*2,c]};
 if(t===2||t===3)return {...base,status:'pending'};
 const across=t===4||t===5?hx:y;
 if(across<lo||across>hi)return {...base,status:'miss',reason:'range'};
 let target,coordinate,axis,limit,scale;
 if(t<2){let q=Math.trunc(wordSigned(a)*y/wordSigned(b));if(!Number.isFinite(q)||q< -32768||q>32767)return {...base,status:'pending'};target=wordSigned((q+wordSigned(c))*2);coordinate=x;axis='x';limit=15;scale=1;}
 else if(t<6){target=a;coordinate=y;axis='y';limit=8;scale=1;}
 else {target=a;coordinate=hx;axis='x';limit=8;scale=2;}
 const delta=wordSigned(coordinate-target);let hit=(delta===0||Number(delta<0)===(t&1))&&Math.abs(delta)<limit;
 return {...base,status:hit?'contact':'miss',axis,target:target*scale,delta,scale,limit};
}
function offsetVelocity(v,ramWord,axis){v|=0;let w=wordSigned(ramWord);if(!w)return v;let n=(v+w*(axis==='x'?512:256))|0;return ((n^v)<0)?0:n;}
function axisResponse(r,position,velocity,ram={}){
 const h=straight12(r,position[0]>>>16,position[1]>>>16),t=h.type;
 const unchanged=(status,reason)=>({...h,status,reason,position:[...position],velocity:[...velocity]});
 if(h.status!=='contact'||t<4||t>7)return unchanged(h.status,'not an axis contact');
 const axis=t<6?'y':'x',i=axis==='y'?1:0,negativeFlag=!!(r[0]&0x8000),id=r[7]&255;
 if((axis==='x'||negativeFlag)&&Number((velocity[i]>>16)<0)!==(t&1))return unchanged('rejected','velocity direction');
 let p=[...position],v=[...velocity];if(negativeFlag)p[i]=(p[i]-h.delta*h.scale*65536)|0;
 if((r[0]&0x4000)||r[7]>>>8)return {...h,status:'pending-event',reason:'guard or event callback needs game state',position:p,velocity:v};
 let shift=axis==='y'?[1,2,4][id]:({1:3,2:3})[id];
 if(axis==='x'&&id===0)return {...h,status:'no-op',position:p,velocity:v};
 if(shift===undefined)return {...h,status:'pending-event',reason:'stateful callback',position:p,velocity:v};
 const adjusted=offsetVelocity(v[i],axis==='x'?(ram.x||0):(ram.y||0),axis);
 v[i]=((-adjusted)|0)>>shift;
 return {...h,status:'reflected',axis,shift,adjusted,position:p,velocity:v};
}
if(typeof module!=='undefined')module.exports={straight12,offsetVelocity,axisResponse};
