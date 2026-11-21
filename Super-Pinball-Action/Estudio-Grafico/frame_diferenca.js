/* Pixel-accurate difference between two already-rendered canvas snapshots.
 * It marks change regions for diagnostics; it does not move or modify ROM art.
 * UMD: Browser global SpaFrameDifference; independent of DOM.
 */
(function(root){
"use strict";
function compare(a,b){
 if(!a||!b||a.width!==b.width||a.height!==b.height||
    !a.data||!b.data||a.data.length!==b.data.length||
    a.data.length!==a.width*a.height*4||a.width<=0||a.height<=0)
   throw new Error("Invalid frame comparison buffers");
 const w=a.width,h=a.height,n=w*h,out=new Uint8ClampedArray(n*4);
 let changed=0,left=0,right=0,minX=w,minY=h,maxX=-1,maxY=-1;
 for(let i=0;i<n;i++){
  const j=i*4;
  if(a.data[j]===b.data[j]&&a.data[j+1]===b.data[j+1]&&
     a.data[j+2]===b.data[j+2]&&a.data[j+3]===b.data[j+3])continue;
  const x=i%w,y=(i/w)|0;
  if(x<w/2)left++;else right++;
  changed++;minX=Math.min(minX,x);minY=Math.min(minY,y);
  maxX=Math.max(maxX,x);maxY=Math.max(maxY,y);
  out[j]=250;out[j+1]=199;out[j+2]=40;out[j+3]=165;
 }
 return {rgba:out,changedPixels:changed,leftPixels:left,rightPixels:right,
  bounds:changed?{x:minX,y:minY,width:maxX-minX+1,height:maxY-minY+1}:null};
}
root.SpaFrameDifference=Object.freeze({compare});
})(globalThis);
