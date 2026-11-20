'use strict';
// US ROM: isolated static, flagged contacts; RAM adjustment words assumed zero.
// Does not execute stateful callbacks, dynamic flipper response, or a CPU interpreter.
const projectSign = v => v < 0 ? 1 : 0;
function project13(kind,angle,velocity,geometrySign,coefficients){
 if(!Number.isInteger(angle)||angle<0||angle>255)throw RangeError('angle');
 const vx=velocity[0]|0,vy=velocity[1]|0;
 const a=coefficients.cross[angle]&65535,b=coefficients.square[angle]&65535;
 const x=((Math.abs(vx)>>>0)>>>8)&65535,y=((Math.abs(vy)>>>0)>>>7)&65535;
 const mul=(u,v)=>Math.imul(u,v)>>>8;
 let d1,d2,d3=mul(x,a),d4=mul(y,a);
 if(kind==='slope'){
  d1=mul(y,b);d2=mul(x,(-b)&65535);
  if(vx<0){d2=-d2;d3=-d3}if(vy<0){d1=-d1;d4=-d4}
  if(!geometrySign){d3=-d3;d4=-d4}
  return [(d1+d3)|0,(d2+d4)|0];
 }
 d1=mul(x,b);d2=mul(y,(-b)&65535);
 if(vx<0){d1=-d1;d3=-d3}if(vy<0){d2=-d2;d4=-d4}
 if(geometrySign===1||geometrySign===2){d3=-d3;d4=-d4}
 return [(d1+d4)|0,(d2+d3)|0];
}
function rebound13(kind,projection,velocity,callback){
 const [d1,d2]=projection;let a=kind==='slope'?d1:d2,b=kind==='slope'?d2:d1;
 const modes=kind==='slope'?{2:2,3:4,4:3}:{2:1,3:4,5:'threeQuarter',7:3,8:2,9:'fiveEighth'};
 const shift=modes[callback];if(shift===undefined)return null;
 const damp=v=>{const n=(-v)|0;return shift==='threeQuarter'?(n-(n>>2))|0:shift==='fiveEighth'?(n-3*(n>>3))|0:n>>shift};
 return [(velocity[0]-(a>>1)+damp(a>>1))|0,(velocity[1]-b+damp(b))|0];
}
function obliqueResponse13(r,position,velocity,data,options={}){
 const t=r[0]&15,curve=t===2||t===3;
 if(t>3)throw RangeError('not oblique');
 const h=curve?curveSurface(r,position[0],position[1],data.curveTables):straight12(r,position[0]>>>16,position[1]>>>16);
 const ret=(status,extra={})=>({...h,status,position:[...position],velocity:[...velocity],...extra});
 if(h.status!=='contact')return ret(h.status);
 if(!(r[0]&0x8000)||r[0]&0x4000||options.dynamic)return ret('pending-event',{reason:'unflagged, guarded or dynamic contact'});
 if(options.ramX||options.ramY)return ret('pending-event',{reason:'nonzero RAM correction not ported'});
 let angle,geometrySign,accept,p=[...position];
 if(curve){
  const dx=(position[0]>>>17)-r[4],dy=(position[1]>>>16)-r[3];
  geometrySign=(dy<0?1:0)|(dx<0?2:0);angle=h.axis==='y'?(-h.coefficient)&255:h.coefficient;
  const i=h.axis==='x'?0:1;p[i]=(p[i]+h.correctionFixed)|0;
 }else{angle=r[6];geometrySign=(r[3]&32768)?1:0;p[0]=(p[0]-h.delta*65536)|0;}
 const kind=curve?'curve':'slope',q=project13(kind,angle,velocity,geometrySign,data.projection13);
 const [s1,s2]=q.map(projectSign);
 if(curve)accept=t===2?(s1!==((geometrySign>>1)&1)&&s2!==(geometrySign&1)):(s1===((geometrySign>>1)&1)&&s2===(geometrySign&1));
 else accept=s2===(t&1)&&Boolean(s1^(t&1)^geometrySign);
 if(!accept)return ret('rejected',{reason:'projection direction',projection:q,angle});
 if(r[7]>255)return ret('pending-event',{reason:'event high byte',projection:q,angle});
 const v=rebound13(kind,q,velocity,r[7]);
 if(!v)return ret('pending-event',{reason:'callback not ported',projection:q,angle});
 return ret('reflected',{position:p,velocity:v,projection:q,angle,callback:r[7]});
}
if(typeof module!=='undefined'){
 const {curveSurface}=require('./curve'),{straight12}=require('./response');globalThis.curveSurface=curveSurface;globalThis.straight12=straight12;
 module.exports={project13,rebound13,obliqueResponse13};
}
