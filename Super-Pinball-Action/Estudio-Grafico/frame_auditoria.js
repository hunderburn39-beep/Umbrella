/* Diagnóstico de fotogramas / posições ROM, sem física nem alteração de PNG.
 * Pure helpers; runs in browser and node vm for regression testing.
 */
(function(root){
"use strict";
const modes=["both","left","right"];
function framePair(mode,frame,leftFixed=0,rightFixed=0){
 if(!modes.includes(mode)||!Number.isInteger(frame)||frame<0||frame>6||
    !Number.isInteger(leftFixed)||leftFixed<0||leftFixed>6||
    !Number.isInteger(rightFixed)||rightFixed<0||rightFixed>6)
   throw new Error("Invalid frame comparison parameters");
 return {left:mode==="right"?leftFixed:frame,right:mode==="left"?rightFixed:frame};
}
function report(layout,records,map,bank,mode="both",leftFixed=0,rightFixed=0){
 if(!layout||!Array.isArray(layout.maps)||!Array.isArray(layout.rows)||
    !Number.isInteger(map)||map<0||map>=layout.maps.length||
    !Number.isInteger(bank)||bank<0||bank>3)throw new Error("Invalid ROM layout");
 const list=Array.isArray(records)?records:Array.from(records.values());
 const lookup=new Map(list.map(r=>[r.selector+":"+r.frame,r]));
 const selectors=layout.maps[map].selectors;
 const sheet=[];
 for(let frame=0;frame<7;frame++){
  const pair=framePair(mode,frame,leftFixed,rightFixed);
  sheet.push({frame,leftFrame:pair.left,rightFrame:pair.right,groups:selectors.map(selector=>{
   const layoutRow=layout.rows.find(r=>r.selector===selector);
   if(!layoutRow)throw new Error("Unknown selector");
   const chosen=layoutRow.channel==="left"?pair.left:pair.right;
   const r=lookup.get(selector+":"+chosen);
   if(!r||r.pieces.length!==2||r.side!==layoutRow.channel)throw new Error("Incomplete OAM");
   const pieces=r.pieces.map(p=>({
    tile:p.tile,
    romX:p.romX,romY:p.romY,
    screenX:208-p.romY,screenY:p.romX,
    width:32,height:32,
    priority:(p.attributes_base>>4)&3,
    blendBase:!!(p.attributes_base&0x40),
    flipX:!!(p.attributes_base&1),flipY:!!(p.attributes_base&2)
   }));
   return {selector,side:r.side,
    screenRect:{x:layoutRow.displayRect.x,y:layoutRow.displayRect.y,width:32,height:64},
    pieces};
  })});
 }
 return {schema:1,game:layout.game,romSha256:layout.romSha256,map,bank,mode,
  fixedFrames:{left:leftFixed,right:rightFixed},frames:sheet,
  note:"Coordenadas e prioridades base da ROM. Paletas, atributos de mistura dinâmicos e estado real de RAM não reconstruídos."};
}
root.SpaFrameAudit=Object.freeze({framePair,report});
})(globalThis);
