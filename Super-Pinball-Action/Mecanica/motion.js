'use strict';
// Direct partial translations of US ROM. No CPU emulator.
function readControls(in0,in1,system,previous=0){
 let lo=0;
 if((in0&0x10)===0)lo|=1;
 if((in1&0x20)===0)lo|=2;
 if((in0&0x20)===0||(in1&0x10)===0)lo|=8;
 const current=(((system^0xfc)&255)<<8)|lo;
 return {current,previous:previous&65535,pressed:current&~previous&65535,released:previous&~current&65535};
}
function lookupIndex(word0,word4){
 // B18: SUB.L #$10001010 (six bytes); no state-byte substitution.
 const d=((((word0&65535)<<16)|(word4&65535))-0x10001010)>>>0;
 const index=((((d&65535)>>>3)<<5)+((d>>>16)>>>4))&65535;
 return (index<<16)>>16;
}
function applyImpulse(code,table,atA2,atA2Plus4){
 const pair=table[code&63];if(!pair)throw RangeError('Unverified table index: '+(code&63));
 return {atA2:(atA2+pair[1])|0,atA2Plus4:(atA2Plus4+pair[0])|0,flags:(code&0xc0)>>>2};
}
if(typeof module!=='undefined')module.exports={readControls,lookupIndex,applyImpulse};
