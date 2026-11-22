/* Fortuna V8: Babylon scene with dimensions from original SlotScene.tsx.
   Only presentation: V7 rules and virtual-credit state stay authoritative. */
(function(){
"use strict";
window.startFortuna3D=function(){
 if(window.fortuna3DStarting)return;window.fortuna3DStarting=true;
 var canvas=document.getElementById("scene3d"),note=document.getElementById("engineNote");
 var B=window.BABYLON,engine,scene;
 function fallback(msg){window.fortuna3DReady=false;canvas.dataset.ready="false";document.body.classList.remove("real3d");note.textContent="Modo 2D de segurança: "+msg;try{if(engine)engine.dispose()}catch(_){}}
 try{
 if(!B||!B.Engine.isSupported())throw Error("WebGL indisponível");
 engine=new B.Engine(canvas,true,{preserveDrawingBuffer:false,stencil:false,disableWebGL2Support:false});
 engine.setHardwareScalingLevel(Math.max(1,window.devicePixelRatio/1.5));
 scene=new B.Scene(engine);scene.useRightHandedSystem=true;
 scene.clearColor=new B.Color4(10/255,6/255,7/255,1);scene.fogMode=B.Scene.FOGMODE_LINEAR;scene.fogColor=C0();function C0(){return new B.Color3(10/255,6/255,7/255)}scene.fogStart=12;scene.fogEnd=34;
 var V=(x,y,z)=>new B.Vector3(x,y,z),C=h=>B.Color3.FromHexString(h);
 var cam=new B.ArcRotateCamera("camera",Math.PI/2-.32,1.45,9,V(0,2.25,0),scene);
 cam.fov=38*Math.PI/180;cam.minZ=.1;cam.maxZ=80;cam.wheelPrecision=1e6;cam.pinchPrecision=1e6;cam.angularSensibilityX=1400;cam.angularSensibilityY=1400;
 cam.lowerAlphaLimit=Math.PI/2-.7;cam.upperAlphaLimit=Math.PI/2+.7;
 cam.lowerBetaLimit=1.15;cam.upperBetaLimit=1.62;
 cam.panningSensibility=0;cam.lowerRadiusLimit=cam.upperRadiusLimit=9;
 cam.attachControl(canvas,true);
 var hemi=new B.HemisphericLight("ambient",V(0,1,.5),scene);hemi.intensity=.85;hemi.groundColor=C("#58404b");
 var key=new B.DirectionalLight("key",V(-.5,-1,-1),scene);key.intensity=1.3;
 var rim=new B.PointLight("rim",V(-3,4,4),scene);rim.diffuse=C("#ffcc90");rim.intensity=.8;
 var face=new B.PointLight("face",V(1,3,4),scene);face.intensity=.5;
 function mat(n,color,shine,emit){var m=new B.StandardMaterial(n,scene);m.diffuseColor=C(color);m.specularColor=C(shine?"#ffffff":"#343434");m.specularPower=shine||32;if(emit)m.emissiveColor=C(emit);return m}
 function pbr(n,color,metal,rough,coat){var m=new B.PBRMaterial(n,scene);m.albedoColor=C(color);m.metallic=metal;m.roughness=rough;if(coat){m.clearCoat.isEnabled=true;m.clearCoat.intensity=1;m.clearCoat.roughness=.08}m.environmentIntensity=1.25;return m}
 var paint=pbr("red lacquer","#8a0f19",.35,.32,true),chrome=pbr("chrome","#e6e6e6",1,.1),gold=pbr("gold","#d6a844",1,.22),black=pbr("black","#0d0b0c",.2,.55),red=pbr("red","#c3121c",.15,.15,true),amber=mat("amber","#f0a52a",80),paper=mat("paper","#cfc3a6",8),glass=mat("glass","#ffffff",128);
 // Independent reflection environment: five studio light panels matching the source positions.
 try{var probe=new B.ReflectionProbe("studio",128,scene),panels=[];var specs=[[0,6,2,8,2,"#fff4dd"],[-5,2,3,10,1.2,"#ffcf8a"],[5,1.5,1,10,.8,"#ff5a4a"],[0,2,8,6,3,"#ffffff"],[0,-1,4,8,2,"#ffb070"]];specs.forEach((p,i)=>{var o=B.MeshBuilder.CreatePlane("studio"+i,{width:p[3],height:p[4],sideOrientation:B.Mesh.DOUBLESIDE},scene);o.position=V(p[0],p[1],p[2]);o.lookAt(V(0,2,0));var m=mat("studio light"+i,p[5],8,p[5]);m.disableLighting=true;o.material=m;o.layerMask=0x10000000;o.isPickable=false;panels.push(o)});probe.renderList=panels;probe.position=V(0,2,0);probe.cubeTexture.onBeforeRenderObservable.add(()=>{panels.forEach(o=>o.layerMask=0x0fffffff)});probe.cubeTexture.onAfterRenderObservable.add(()=>{panels.forEach(o=>o.layerMask=0x10000000)});probe.cubeTexture.refreshRate=B.RenderTargetTexture.REFRESHRATE_RENDER_ONCE;scene.environmentTexture=probe.cubeTexture;}catch(e){console.warn("Reflection environment",e)}
 glass.alpha=.06;glass.backFaceCulling=false;glass.disableDepthWrite=true;
 function box(n,x,y,z,w,h,d,m,parent){var o=B.MeshBuilder.CreateBox(n,{width:w,height:h,depth:d},scene);o.position=V(x,y,z);o.material=m;if(parent)o.parent=parent;return o}
 // RoundedBox equivalent: a subdivided six-face shell projected onto a rounded cuboid.
 function rounded(n,x,y,z,w,h,d,r,m){var half=[w/2,h/2,d/2],inner=half.map(v=>v-r),pos=[],norm=[],uv=[],indices=[],N=5;
 for(var axis=0;axis<3;axis++){for(var sign of [-1,1]){var u=(axis+1)%3,v=(axis+2)%3,base=pos.length/3;
 var coords=k=>[-half[k],-inner[k]-r*.7071,-inner[k],0,inner[k],inner[k]+r*.7071,half[k]];
 var us=coords(u),vs=coords(v);N=us.length-1;
 for(var j=0;j<=N;j++)for(var i=0;i<=N;i++){var p=[0,0,0];p[axis]=sign*half[axis];p[u]=us[i];p[v]=vs[j];var q=p.map((a,k)=>Math.max(-inner[k],Math.min(inner[k],a))),delta=p.map((a,k)=>a-q[k]),len=Math.hypot(...delta);var normal=delta.map(a=>a/len);pos.push(...q.map((a,k)=>a+r*normal[k]));norm.push(...normal);uv.push(i/N,j/N)}
 for(var j=0;j<N;j++)for(var i=0;i<N;i++){var a=base+j*(N+1)+i,b=a+1,c=a+N+1,e=c+1;if(sign>0)indices.push(a,b,c,b,e,c);else indices.push(a,c,b,b,c,e)}
 }}
 var o=new B.Mesh(n,scene),data=new B.VertexData();data.positions=pos;data.normals=norm;data.uvs=uv;data.indices=indices;data.applyToMesh(o);o.position=V(x,y,z);o.material=m.clone(n+" material");o.material.backFaceCulling=false;return o}
 function cylinder(n,x,y,z,d,h,m,parent){var o=B.MeshBuilder.CreateCylinder(n,{diameter:d,height:h,tessellation:24},scene);o.position=V(x,y,z);o.material=m;if(parent)o.parent=parent;return o}
 function ball(n,x,y,z,d,m,parent){var o=B.MeshBuilder.CreateSphere(n,{diameter:d,segments:12},scene);o.position=V(x,y,z);o.material=m;if(parent)o.parent=parent;return o}
 function texture(n,w,h,draw){var t=new B.DynamicTexture(n,{width:w,height:h},scene,false);var c=t.getContext();draw(c,w,h);t.update();return t}
 function texmat(n,t,emissive){var m=mat(n,"#ffffff",12);m.diffuseTexture=t;m.backFaceCulling=false;if(emissive){m.emissiveTexture=t;m.emissiveColor=C("#ffffff")}return m}
 function plane(n,x,y,z,w,h,m,parent){var o=B.MeshBuilder.CreatePlane(n,{width:w,height:h,sideOrientation:B.Mesh.DOUBLESIDE},scene);o.position=V(x,y,z);o.material=m;if(parent)o.parent=parent;return o}
 var snapshot=window.fortunaState(),step=Math.PI*2/20,cell=2*.8*Math.tan(step/2),reels=[],bulbs=[],lineMeshes=[],coins=[];
 var glyph={CH:"🍒",LE:"🍋",OR:"🍊",GR:"🍇",BE:"🔔",ST:"⭐",SE:"7"},symbols={};
 Object.keys(glyph).forEach(id=>{
 var t=texture("symbol-"+id,512,Math.round(512/(.58/cell)),(c,w,h)=>{var g=c.createLinearGradient(0,0,0,h);g.addColorStop(0,"#efe4cc");g.addColorStop(.5,"#fffaf0");g.addColorStop(1,"#efe4cc");c.fillStyle=g;c.fillRect(0,0,w,h);for(let k=0;k<2500;k++){c.fillStyle="rgba("+(Math.random()>.5?"0,0,0":"255,255,255")+","+(.06*Math.random())+")";c.fillRect(Math.random()*w,Math.random()*h,1.5,1.5)}c.fillStyle="rgba(120,95,60,.35)";c.fillRect(0,0,w,2);c.fillRect(0,h-2,w,2);c.textAlign="center";c.textBaseline="middle";if(id==="SE"){c.font=Math.round(h*.9)+"px Bungee, Impact, sans-serif";c.lineJoin="round";c.lineWidth=14;c.strokeStyle="#b8862b";c.strokeText("7",w/2,h*.54);var redg=c.createLinearGradient(0,h*.15,0,h*.9);redg.addColorStop(0,"#ff4a3d");redg.addColorStop(1,"#9c0f12");c.fillStyle=redg;c.fillText("7",w/2,h*.54)}else{c.font=Math.round(h*.78)+'px "Apple Color Emoji","Segoe UI Emoji","Noto Color Emoji",sans-serif';c.shadowColor="rgba(0,0,0,.25)";c.shadowBlur=8;c.shadowOffsetY=4;c.fillText(glyph[id],w/2,h*.54)}});symbols[id]=texmat(id,t,false);symbols[id].emissiveColor=C("#55504a");
 });
 rounded("pedestal",0,.45,0,2.55,.9,1.95,.06,black);
 box("base trim",0,.87,.98,2.55,.05,.025,gold);
 box("lower",0,1.5125,0,2.4,1.225,1.8,paint);
 box("upper",0,3.2625,0,2.4,.375,1.8,paint);
 rounded("marquee",0,3.925,0,2.4,.95,1.8,.08,paint);
 box("back",0,2.6,-.84,1.95,.95,.12,black);
 [-1,1].forEach(s=>{box("pillar",s*1.0875,2.6,0,.225,.95,1.8,paint);cylinder("edge",s*1.2,2.175,.9,.07,2.55,chrome);box("window vertical",s*1.005,2.6,.92,.06,1.07,.05,chrome)});
 [2.095,3.105].forEach(y=>box("window horizontal",0,y,.92,2.07,.06,.05,chrome));
 [-.32,.32].forEach(x=>box("separator",x,2.6,.2,.05,.95,1.3,black));
 box("upper trim",0,3.4,.91,2.4,.07,.025,gold);
 box("chute",0,1.58,.91,.8,.16,.028,black);
 box("chute trim",0,1.67,.93,.9,.035,.04,chrome);
 box("tray",0,1.285,1.08,1.26,.03,.39,chrome);
 box("tray front",0,1.32,1.28,1.26,.06,.04,chrome);
 [-1,1].forEach(s=>box("tray side",s*.615,1.32,1.08,.03,.06,.39,chrome));
 var deck=rounded("deck",0,1.925,1.12,2.3,.10,.45,.03,black);deck.rotation.x=.28;
 box("deck lip",0,1.91,1.345,2.3,.06,.025,chrome);
 var marquee=texture("marquee",1024,360,(c,w,h)=>{var g=c.createRadialGradient(w/2,h/2,20,w/2,h/2,w*.6);g.addColorStop(0,"#7a0d16");g.addColorStop(1,"#22040a");c.fillStyle=g;c.fillRect(0,0,w,h);c.save();c.translate(w/2,h*.55);for(let i=0;i<36;i++){c.rotate(Math.PI*2/36);c.fillStyle=i%2?"#ffc85a12":"#0001";c.beginPath();c.moveTo(0,0);c.lineTo(w,-40);c.lineTo(w,40);c.fill()}c.restore();c.textAlign="center";c.textBaseline="middle";c.font="150px Bungee, Impact, sans-serif";c.lineJoin="round";c.lineWidth=18;c.strokeStyle="#2a0508";c.strokeText("FORTUNA",w/2,h*.4);var gg=c.createLinearGradient(0,h*.18,0,h*.62);gg.addColorStop(0,"#fff3b8");gg.addColorStop(.5,"#f2c14e");gg.addColorStop(1,"#a8701c");c.fillStyle=gg;c.shadowColor="rgba(255,190,60,.8)";c.shadowBlur=24;c.fillText("FORTUNA",w/2,h*.4);c.shadowBlur=0;c.font="92px Bungee, Impact, sans-serif";c.lineWidth=12;c.strokeText("777",w/2,h*.78);var rg=c.createLinearGradient(0,h*.66,0,h*.92);rg.addColorStop(0,"#ff6b52");rg.addColorStop(1,"#c4141a");c.fillStyle=rg;c.fillText("777",w/2,h*.78)});
 plane("title",0,3.93,.913,2.05,.72,texmat("marquee material",marquee,true));
 var bulbA=mat("bulbs A","#ffcf6b",30,"#ffcf6b"),bulbB=mat("bulbs B","#ffcf6b",30,"#ffcf6b");
 for(let i=0;i<=13;i++)for(let y of [3.54,4.32])bulbs.push(ball("bulb",-1.06+2.12*i/13,y,.94,.076,i%2?bulbA:bulbB));
 for(let i=1;i<4;i++)for(let x of [-1.06,1.06])bulbs.push(ball("bulb",x,3.54+.78*i/4,.94,.076,i%2?bulbA:bulbB));
 var towerR=mat("tower red","#5a0505",40,"#ff2a1a"),towerW=mat("tower white","#666666",40,"#fff4dc");cylinder("tower base",.9,4.43,0,.2,.06,chrome);cylinder("tower red",.9,4.55,0,.15,.18,towerR);cylinder("tower white",.9,4.73,0,.15,.18,towerW);ball("tower cap",.9,4.84,0,.156,chrome);
 var ledMats=[mat("LED left","#000000",10,"#ffb040"),mat("LED right","#000000",10,"#ffb040")];[-1,1].forEach((sg,i)=>{box("side LED",sg*1.204,2.175,.8,.012,2.45,.035,ledMats[i]);[[0,3.15,1.3,.025],[0,1.1,1.3,.025],[-.65,2.125,.025,2.05],[.65,2.125,.025,2.05]].forEach(a=>box("side gold pinstripe",sg*1.203,a[1],a[0]-.05,.006,a[3],a[2],gold))});
 box("acceptor",.82,1.6,.91,.2,.26,.02,chrome);box("coin slot",.82,1.65,.921,.025,.1,.004,black);box("acceptor light",.82,1.52,.922,.13,.018,.004,mat("acceptor green","#000000",8,"#35ff7a"));box("base underglow",0,.03,.98,2.5,.02,.01,mat("underglow","#000000",8,"#ff5a2a"));
 
 snapshot.reels.forEach((strip,i)=>{var group=new B.TransformNode("reel"+i,scene);group.position=V([-.64,0,.64][i],2.6,.05);var drum=cylinder("drum",0,0,0,1.552,.568,paper,group);drum.rotation.z=Math.PI/2;
 strip.forEach((id,j)=>{var pivot=new B.TransformNode("cell"+i+"-"+j,scene);pivot.parent=group;pivot.rotation.x=j*step;plane("symbol",0,0,.8,.58,cell,symbols[id],pivot)});
 [-1,1].forEach(s=>{var hub=cylinder("hub cap",s*(.58/2+.005),0,0,1.584,.01,black,group);hub.rotation.z=Math.PI/2});reels.push(group);
 });
 plane("glass",0,2.6,.906,1.95,.95,glass);
 var lineColors=["#ff3030","#ffc83a","#35d0c0","#5be05e","#ff8a2a"];
 snapshot.paths.forEach((p,i)=>{var row=[.8*Math.sin(step),0,-.8*Math.sin(step)],pts=[V(-.955,2.6+row[p[0]],.944),...p.map((r,j)=>V([-.64,0,.64][j],2.6+row[r],.944)),V(.955,2.6+row[p[2]],.944)];var m=mat("line"+i,lineColors[i],10,lineColors[i]);var tube=B.MeshBuilder.CreateTube("line"+i,{path:pts,radius:.009,tessellation:6},scene);tube.material=m;tube.setEnabled(false);lineMeshes.push(tube)});
 var leverPivot=new B.TransformNode("lever pivot",scene);leverPivot.position=V(1.44,2.15,.15);var lvbase=cylinder("lever base",1.3,2.15,.15,.32,.2,chrome);lvbase.rotation.z=Math.PI/2;
 var rod=cylinder("lever",0,.6,0,.065,1.2,chrome,leverPivot);var knob=ball("lever knob",0,1.25,0,.26,red,leverPivot);
 function clickMesh(o,action){o.actionManager=new B.ActionManager(scene);o.actionManager.registerAction(new B.ExecuteCodeAction(B.ActionManager.OnPickTrigger,action))}
 clickMesh(knob,()=>document.getElementById("lever").click());clickMesh(rod,()=>document.getElementById("lever").click());
 var deckButtons=new B.TransformNode("button group",scene);deckButtons.position=V(0,1.925,1.12);deckButtons.rotation.x=.28;[-.75,-.45,.6].forEach((x,i)=>{var r=i===2?.13:.07;cylinder("button rim",x,.05,.02,r*2.5,.04,chrome,deckButtons);var cap=cylinder("button",x,.09,.02,r*2,.07,i===2?red:amber,deckButtons);clickMesh(cap,()=>{document.getElementById(["down","bet","spin"][i]).click();cap.position.y=.065;setTimeout(()=>cap.position.y=.09,150)})});
 var carpet=texture("carpet",256,256,(c,w,h)=>{c.fillStyle="#2a080e";c.fillRect(0,0,w,h);c.strokeStyle="#8a6a2c";c.lineWidth=3;c.beginPath();c.moveTo(w/2,10);c.lineTo(w-10,h/2);c.lineTo(w/2,h-10);c.lineTo(10,h/2);c.closePath();c.stroke();c.fillStyle="#0d3236";c.beginPath();c.arc(w/2,h/2,34,0,Math.PI*2);c.fill();c.fillStyle="#8a6a2c";[[0,0],[w,0],[0,h],[w,h]].forEach(p=>{c.beginPath();c.arc(p[0],p[1],18,0,Math.PI*2);c.fill()});for(let k=0;k<6000;k++){c.fillStyle="rgba("+(Math.random()>.5?"0,0,0":"255,255,255")+","+(.25*Math.random())+")";c.fillRect(Math.random()*w,Math.random()*h,1.5,1.5)}});carpet.uScale=carpet.vScale=26;carpet.wrapU=carpet.wrapV=B.Texture.WRAP_ADDRESSMODE;
 var floor=B.MeshBuilder.CreateGround("floor",{width:60,height:60},scene);floor.material=texmat("carpet",carpet,false);
 // Recreate the source's floor contact shadow and distant casino light sprites, without costly full-screen effects.
 var contactTex=texture("contact shadow",256,256,(c,w,h)=>{var g=c.createRadialGradient(w/2,h/2,16,w/2,h/2,w/2);g.addColorStop(0,"rgba(0,0,0,.8)");g.addColorStop(.37,"rgba(0,0,0,.65)");g.addColorStop(1,"rgba(0,0,0,0)");c.fillStyle=g;c.fillRect(0,0,w,h)});contactTex.hasAlpha=true;var contactMat=texmat("contact",contactTex,false);contactMat.useAlphaFromDiffuseTexture=true;contactMat.disableLighting=true;contactMat.disableDepthWrite=true;var contact=B.MeshBuilder.CreateGround("contact",{width:5.5,height:4.8},scene);contact.position.y=.006;contact.material=contactMat;
 var glowTex=texture("casino glow",64,64,(c)=>{var g=c.createRadialGradient(32,32,0,32,32,32);g.addColorStop(0,"rgba(255,255,255,1)");g.addColorStop(.35,"rgba(255,255,255,.55)");g.addColorStop(1,"rgba(255,255,255,0)");c.fillStyle=g;c.fillRect(0,0,64,64)});glowTex.hasAlpha=true;
 var seed=7;function rand(){seed=(seed+0x6d2b79f5)|0;let t=Math.imul(seed^(seed>>>15),1|seed);t=(t+Math.imul(t^(t>>>7),61|t))^t;return ((t^(t>>>14))>>>0)/4294967296}
 var pal=["#ffb347","#ff5a45","#3fc6bd","#ffe2a8"];
 for(let i=0;i<40;i++){let x=(rand()-.5)*40,y=1+rand()*7,z=-14-rand()*14,r=.5+rand()*1.1,color=pal[Math.floor(rand()*4)],opacity=.06+rand()*.16;let m=mat("bokeh"+i,color,8,color);m.diffuseTexture=glowTex;m.opacityTexture=glowTex;m.useAlphaFromDiffuseTexture=true;m.alpha=opacity;m.alphaMode=B.Engine.ALPHA_ADD;m.disableLighting=true;m.disableDepthWrite=true;let o=plane("distant light",x,y,z,r,r,m);o.billboardMode=B.Mesh.BILLBOARDMODE_ALL;o.isPickable=false}
 
 var displayTex=new B.DynamicTexture("display",{width:1024,height:140},scene,false),display=plane("display",0,3.2625,.923,1.64,.2,texmat("display",displayTex,true));box("display frame",0,3.2625,.912,1.72,.25,.02,black);
 var coinMaterial=pbr("coin","#f4c654",1,.2);coinMaterial.environmentIntensity=1.8;
 var wasBusy=false,lastDisplay="",ready=false,frames=0,lastTime=performance.now()/1000;
 var glow=new B.GlowLayer("cabinet glow",scene,{mainTextureFixedSize:256,blurKernelSize:24});glow.intensity=.32;
 var flash=new B.PointLight("win flash",V(0,2.6,2.1),scene);flash.diffuse=C("#ffc24a");flash.intensity=0;
 var streak=texture("glass streak",256,128,(c,w,h)=>{var g=c.createLinearGradient(0,0,w,h);[[.18,0],[.26,.9],[.33,0],[.42,0],[.45,.5],[.49,0]].forEach(a=>g.addColorStop(a[0],"rgba(255,255,255,"+a[1]+")"));c.fillStyle=g;c.fillRect(0,0,w,h)});streak.hasAlpha=true;
 var streakMat=texmat("glass reflection",streak,true);streakMat.alpha=.14;streakMat.useAlphaFromDiffuseTexture=true;streakMat.disableDepthWrite=true;plane("glass reflection",0,2.6,.921,1.95,.95,streakMat);
 var shade=texture("window shade",4,256,(c,w,h)=>{var g=c.createLinearGradient(0,0,0,h);[[0,.8],[.2,0],[.8,0],[1,.8]].forEach(a=>g.addColorStop(a[0],"rgba(20,12,10,"+a[1]+")"));c.fillStyle=g;c.fillRect(0,0,w,h)});shade.hasAlpha=true;
 var shadeMat=texmat("window shade",shade,false);shadeMat.useAlphaFromDiffuseTexture=true;shadeMat.disableLighting=true;shadeMat.disableDepthWrite=true;plane("window shadow",0,2.6,.88,1.95,.95,shadeMat);var reelLamp=new B.PointLight("reel warm light",V(0,3.125,.7),scene);reelLamp.diffuse=C("#ffe6bf");reelLamp.intensity=.9;reelLamp.range=2;
 var markerMats=[],markers=[];snapshot.paths.forEach((p,i)=>{var t=texture("marker"+i,64,64,(c)=>{c.fillStyle=lineColors[i];c.beginPath();c.arc(32,32,29,0,Math.PI*2);c.fill();c.font="bold 40px sans-serif";c.textAlign="center";c.textBaseline="middle";c.fillStyle="#1a0a05";c.fillText(String(i+1),32,35)});t.hasAlpha=true;var m=texmat("marker"+i,t,true);m.useAlphaFromDiffuseTexture=true;markerMats.push(m);for(let side of [-1,1]){var row=p[side<0?0:2],other=snapshot.paths.map((q,k)=>({row:q[side<0?0:2],k})).filter(q=>q.row===row).map(q=>q.k),offset=(other.indexOf(i)-(other.length-1)/2)*.095;var o=plane("line marker",side*(1.09+offset),2.6+[.8*Math.sin(step),0,-.8*Math.sin(step)][row],.944,.084,.084,m);markers.push(o)}});
 var sparkMat=mat("spark","#ffd98a",12,"#ffd98a"),sparks=[];
 for(let i=0;i<90;i++){let o=ball("spark",0,0,0,.025,sparkMat);o.isPickable=false;o.setEnabled(false);sparks.push({o,x:(Math.random()-.5),y:(Math.random()-.5),z:Math.random(),phase:Math.random()*6.28})}
 function spawnCoins(count){return Array.from({length:Math.min(70,Math.max(6,count))},(_,i)=>{var mesh=cylinder("coin",0,1.58,.94,.13,.016,coinMaterial);mesh.setEnabled(false);mesh.isPickable=false;return{mesh,p:[(Math.random()-.5)*.5,1.58,.94],v:[(Math.random()-.5)*1.2,Math.random()*.6,.5+Math.random()],rot:[Math.random()*Math.PI,Math.random()*Math.PI,Math.random()*Math.PI],spin:[(Math.random()-.5)*18,(Math.random()-.5)*10,(Math.random()-.5)*18],delay:i*.05,layer:Math.floor(Math.random()*Math.min(5,1+count/12)),resting:false}})}
 function stepCoins(dt){for(const c of coins){if(c.delay>0){c.delay-=dt;continue}c.mesh.setEnabled(true);if(!c.resting){var rest=1.3+.008+c.layer*.016*.9;c.v[1]-=9.8*1.4*dt;for(let k=0;k<3;k++){c.p[k]+=c.v[k]*dt;c.rot[k]+=c.spin[k]*dt}for(let a of [[0,-.6,.6],[2,.91,1.26]]){let k=a[0],lo=a[1]+.065,hi=a[2]-.065;if(c.p[k]<lo){c.p[k]=lo;c.v[k]=Math.abs(c.v[k])*.4}if(c.p[k]>hi){c.p[k]=hi;c.v[k]=-Math.abs(c.v[k])*.4}}if(c.p[1]<=rest){c.p[1]=rest;if(Math.abs(c.v[1])>.7){c.v[1]=-c.v[1]*.3;c.spin=c.spin.map(x=>x*.5)}else{c.v[1]=0;let f=Math.exp(-7*dt);c.v[0]*=f;c.v[2]*=f;c.rot[0]*=f;c.rot[2]*=f;c.spin=[0,c.spin[1]*f,0];if(Math.hypot(c.v[0],c.v[2])<.02){c.rot[0]=c.rot[2]=0;c.resting=true}}}}c.mesh.position.set(...c.p);c.mesh.rotation.set(...c.rot)}}
 
 function fit(){engine.resize();var ratio=canvas.clientWidth/Math.max(1,canvas.clientHeight),v=cam.fov/2,h=Math.atan(Math.tan(v)*ratio),d=Math.max(1.85/Math.tan(h),2.6/Math.tan(v))+1.2,y=ratio<1?1.55:2.25;cam.target=V(0,y,0);cam.lowerRadiusLimit=cam.upperRadiusLimit=Math.hypot(d,.9);cam.radius=cam.lowerRadiusLimit;cam.beta=Math.atan2(d,.9)}
 window.addEventListener("resize",fit);
 canvas.addEventListener("webglcontextlost",function(e){e.preventDefault();fallback("contexto gráfico perdido")});
 scene.executeWhenReady(function(){if(!engine||engine.isDisposed)return;engine.runRenderLoop(function(){try{
 var st=window.fortunaState(),t=performance.now()/1000,dt=Math.min(.05,Math.max(0,t-lastTime));lastTime=t;reels.forEach((r,i)=>r.rotation.x=-(st.reelAngles?st.reelAngles[i]:st.visual[i]*step));lineMeshes.forEach((o,i)=>o.setEnabled(st.wins.some(w=>w.i===i)));
 bulbA.emissiveColor=C("#ffcf6b").scale(.55+Math.max(0,Math.sin(t*(st.last?14:3.2))));bulbB.emissiveColor=C("#ffcf6b").scale(.55+Math.max(0,-Math.sin(t*(st.last?14:3.2))));
 if(st.busy&&!wasBusy)leverPivot.metadata={start:t};var lt=t-(leverPivot.metadata?.start??-10);leverPivot.rotation.x=lt<.22?1.05*lt/.22:lt<.75?1.05*(1-(1+1.9*Math.pow((lt-.22)/.53-1,3)+.9*Math.pow((lt-.22)/.53-1,2))):0;var excited=st.busy||st.last>0;ledMats.forEach((m,i)=>{var hue=excited?(t*.6+i*.5)%1:.07+.03*Math.sin(t*.8+i);m.emissiveColor=B.Color3.FromHSV(hue*360,1,1).scale(excited?2.4:1.4)});var blink=Math.sin(t*(excited?14:2))>0;towerR.emissiveColor=C("#ff2a1a").scale(excited?(blink?3:.3):1.1);towerW.emissiveColor=C("#fff4dc").scale(excited?(blink?.3:3):.5);
 var text=st.balance+"  |  "+st.cost+"  |  "+st.last;if(text!==lastDisplay){lastDisplay=text;var c=displayTex.getContext();c.fillStyle="#070303";c.fillRect(0,0,1024,140);[["CRÉDITO",st.balance,6],["APOSTA",st.cost,3],["PRÉMIO",st.last,5]].forEach((a,i)=>{let x=1024/3*i+1024/6;c.textAlign="center";c.fillStyle="#c99a3a";c.font="600 26px sans-serif";c.fillText(a[0],x,34);c.font="bold 74px monospace";c.fillStyle="rgba(255,60,40,.12)";c.fillText("8".repeat(a[2]),x,116);c.fillStyle="#ff4632";c.shadowColor="#ff2a1a";c.shadowBlur=18;c.fillText(String(Math.min(a[1],10**a[2]-1)).padStart(a[2],"0"),x,116);c.shadowBlur=0});displayTex.update()}
 if(wasBusy&&!st.busy&&st.last>0){coins.forEach(c=>c.mesh.dispose());coins=spawnCoins(Math.round(st.last*1.5))}
 stepCoins(dt);
 var won=st.last>0&&!st.busy,big=won&&st.wins.some(w=>{let p=st.paths[w.i];let ids=p.map((r,j)=>st.reels[j][((Math.round(st.visual[j])+r-1)%20+20)%20]);return ids.every(id=>id===ids[0])});
 flash.intensity=big?1.2+.8*Math.sin(t*16):0;
 sparks.forEach((a,i)=>{let on=i<15||won&&(big||i<55);a.o.setEnabled(on);if(on){let upper=i<15;a.o.position.set(a.x*(upper?2.4:big?4:1.95), (upper?4.15:2.6)+a.y*(upper?.65:big?3.9:.95)+.05*Math.sin(t*3+a.phase),.98+a.z*.25);let k=.5+.5*Math.sin(t*5+a.phase);a.o.scaling.setAll(.3+k)}});
 markerMats.forEach((m,i)=>{m.alpha=i<(st.active||5)?1:.25;m.emissiveColor=C(lineColors[i]).scale(st.wins.some(w=>w.i===i)?1+.5*Math.sin(t*10):i<(st.active||5)?.55:.08)});
 wasBusy=st.busy;scene.render();if(!ready&&++frames>=2){ready=true;document.body.classList.add("real3d");note.textContent="V8.4 · Babylon.js 3D";window.fortuna3DReady=true;canvas.dataset.ready="true";fit()}
 }catch(e){fallback(e.message)}});fit()});
 setTimeout(function(){if(!ready)fallback("motor 3D não iniciou")},14000);
 }catch(e){fallback(e.message)}
};
})();
