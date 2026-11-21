/* Fortuna V8: Babylon scene with dimensions from original SlotScene.tsx.
   Only presentation: V7 rules and virtual-credit state stay authoritative. */
(function(){
"use strict";
window.startFortuna3D=function(){
 if(window.fortuna3DStarting)return;window.fortuna3DStarting=true;
 var canvas=document.getElementById("scene3d"),note=document.getElementById("engineNote");
 var B=window.BABYLON,engine,scene;
 function fallback(msg){document.body.classList.remove("real3d");note.textContent="Modo 2D de segurança: "+msg;try{if(engine)engine.dispose()}catch(_){}}
 try{
 if(!B||!B.Engine.isSupported())throw Error("WebGL indisponível");
 engine=new B.Engine(canvas,true,{preserveDrawingBuffer:false,stencil:false,disableWebGL2Support:false});
 engine.setHardwareScalingLevel(Math.max(1,window.devicePixelRatio/1.5));
 scene=new B.Scene(engine);scene.useRightHandedSystem=true;
 scene.clearColor=new B.Color4(.035,.018,.025,1);
 var V=(x,y,z)=>new B.Vector3(x,y,z),C=h=>B.Color3.FromHexString(h);
 var cam=new B.ArcRotateCamera("camera",Math.PI/2-.27,1.36,9,V(0,2.25,0),scene);
 cam.fov=.7;cam.minZ=.1;cam.maxZ=70;
 cam.lowerAlphaLimit=Math.PI/2-.6;cam.upperAlphaLimit=Math.PI/2+.6;
 cam.lowerBetaLimit=1.15;cam.upperBetaLimit=1.57;
 cam.panningSensibility=0;cam.lowerRadiusLimit=cam.upperRadiusLimit=9;
 cam.attachControl(canvas,true);
 var hemi=new B.HemisphericLight("ambient",V(0,1,.5),scene);hemi.intensity=.85;hemi.groundColor=C("#58404b");
 var key=new B.DirectionalLight("key",V(-.5,-1,-1),scene);key.intensity=1.3;
 var rim=new B.PointLight("rim",V(-3,4,4),scene);rim.diffuse=C("#ffcc90");rim.intensity=.8;
 var face=new B.PointLight("face",V(1,3,4),scene);face.intensity=.5;
 function mat(n,color,shine,emit){var m=new B.StandardMaterial(n,scene);m.diffuseColor=C(color);m.specularColor=C(shine?"#ffffff":"#343434");m.specularPower=shine||32;if(emit)m.emissiveColor=C(emit);return m}
 var paint=mat("red lacquer","#8a0f19",96),chrome=mat("chrome","#bfc3c7",128),gold=mat("gold","#d6a844",90),black=mat("black","#0d0b0c",25),red=mat("red","#e3242b",100),amber=mat("amber","#f0a52a",80),paper=mat("paper","#cfc3a6",8),glass=mat("glass","#ffffff",128);glass.alpha=.07;glass.backFaceCulling=false;glass.disableDepthWrite=true;
 function box(n,x,y,z,w,h,d,m,parent){var o=B.MeshBuilder.CreateBox(n,{width:w,height:h,depth:d},scene);o.position=V(x,y,z);o.material=m;if(parent)o.parent=parent;return o}
 function cylinder(n,x,y,z,d,h,m,parent){var o=B.MeshBuilder.CreateCylinder(n,{diameter:d,height:h,tessellation:24},scene);o.position=V(x,y,z);o.material=m;if(parent)o.parent=parent;return o}
 function ball(n,x,y,z,d,m,parent){var o=B.MeshBuilder.CreateSphere(n,{diameter:d,segments:12},scene);o.position=V(x,y,z);o.material=m;if(parent)o.parent=parent;return o}
 function texture(n,w,h,draw){var t=new B.DynamicTexture(n,{width:w,height:h},scene,false);var c=t.getContext();draw(c,w,h);t.update();return t}
 function texmat(n,t,emissive){var m=mat(n,"#ffffff",12);m.diffuseTexture=t;m.backFaceCulling=false;if(emissive){m.emissiveTexture=t;m.emissiveColor=C("#ffffff")}return m}
 function plane(n,x,y,z,w,h,m,parent){var o=B.MeshBuilder.CreatePlane(n,{width:w,height:h,sideOrientation:B.Mesh.DOUBLESIDE},scene);o.position=V(x,y,z);o.material=m;if(parent)o.parent=parent;return o}
 var snapshot=window.fortunaState(),step=Math.PI*2/20,cell=2*.8*Math.tan(step/2),reels=[],bulbs=[],lineMeshes=[],coins=[];
 var glyph={CH:"🍒",LE:"🍋",OR:"🍊",GR:"🍇",BE:"🔔",ST:"⭐",SE:"7"},symbols={};
 Object.keys(glyph).forEach(id=>{
 var t=texture("symbol-"+id,256,112,(c,w,h)=>{var g=c.createLinearGradient(0,0,0,h);g.addColorStop(0,"#efe4cc");g.addColorStop(.5,"#fffaf0");g.addColorStop(1,"#efe4cc");c.fillStyle=g;c.fillRect(0,0,w,h);c.textAlign="center";c.textBaseline="middle";if(id==="SE"){c.font="bold 100px Georgia";c.lineWidth=7;c.strokeStyle="#b8862b";c.strokeText("7",w/2,h*.54);c.fillStyle="#c4141a";c.fillText("7",w/2,h*.54)}else{c.font='87px "Apple Color Emoji","Segoe UI Emoji",sans-serif';c.shadowColor="#0004";c.shadowBlur=5;c.fillText(glyph[id],w/2,h*.54)}});symbols[id]=texmat(id,t,false);symbols[id].emissiveColor=C("#55504a");
 });
 box("pedestal",0,.45,0,2.55,.9,1.95,black);
 box("base trim",0,.87,.98,2.55,.05,.025,gold);
 box("lower",0,1.5125,0,2.4,1.225,1.8,paint);
 box("upper",0,3.2625,0,2.4,.375,1.8,paint);
 box("marquee",0,3.925,0,2.4,.95,1.8,paint);
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
 var deck=box("deck",0,1.925,1.12,2.3,.10,.45,black);deck.rotation.x=.28;
 box("deck lip",0,1.91,1.345,2.3,.06,.025,chrome);
 var marquee=texture("marquee",1024,360,(c,w,h)=>{var g=c.createRadialGradient(w/2,h/2,20,w/2,h/2,w*.6);g.addColorStop(0,"#7a0d16");g.addColorStop(1,"#22040a");c.fillStyle=g;c.fillRect(0,0,w,h);c.save();c.translate(w/2,h*.55);for(let i=0;i<36;i++){c.rotate(Math.PI*2/36);c.fillStyle=i%2?"#ffc85a12":"#0001";c.beginPath();c.moveTo(0,0);c.lineTo(w,-40);c.lineTo(w,40);c.fill()}c.restore();c.textAlign="center";c.textBaseline="middle";c.font="bold 150px Georgia";c.lineWidth=18;c.strokeStyle="#2a0508";c.strokeText("FORTUNA",w/2,h*.4);c.fillStyle="#ffda74";c.fillText("FORTUNA",w/2,h*.4);c.font="bold 92px Georgia";c.fillStyle="#ff4b43";c.fillText("777",w/2,h*.78)});
 plane("title",0,3.93,.913,2.05,.72,texmat("marquee material",marquee,true));
 var bulbA=mat("bulbs A","#ffcf6b",30,"#ffcf6b"),bulbB=mat("bulbs B","#ffcf6b",30,"#ffcf6b");
 for(let i=0;i<=13;i++)for(let y of [3.54,4.32])bulbs.push(ball("bulb",-1.06+2.12*i/13,y,.94,.076,i%2?bulbA:bulbB));
 for(let i=1;i<4;i++)for(let x of [-1.06,1.06])bulbs.push(ball("bulb",x,3.54+.78*i/4,.94,.076,i%2?bulbA:bulbB));
 cylinder("tower base",.84,4.46,0,.18,.13,chrome);var tower=ball("tower",.84,4.57,0,.18,red);
 snapshot.reels.forEach((strip,i)=>{var group=new B.TransformNode("reel"+i,scene);group.position=V([-.64,0,.64][i],2.6,.05);var drum=cylinder("drum",0,0,0,1.552,.568,paper,group);drum.rotation.z=Math.PI/2;
 strip.forEach((id,j)=>{var pivot=new B.TransformNode("cell"+i+"-"+j,scene);pivot.parent=group;pivot.rotation.x=j*step;plane("symbol",0,0,.8,.58,cell,symbols[id],pivot)});
 reels.push(group);
 });
 plane("glass",0,2.6,.906,1.95,.95,glass);
 var lineColors=["#ff3030","#ffc83a","#35d0c0","#5be05e","#ff8a2a"];
 snapshot.paths.forEach((p,i)=>{var row=[.8*Math.sin(step),0,-.8*Math.sin(step)],pts=[V(-.955,2.6+row[p[0]],.944),...p.map((r,j)=>V([-.64,0,.64][j],2.6+row[r],.944)),V(.955,2.6+row[p[2]],.944)];var m=mat("line"+i,lineColors[i],10,lineColors[i]);var tube=B.MeshBuilder.CreateTube("line"+i,{path:pts,radius:.009,tessellation:6},scene);tube.material=m;tube.setEnabled(false);lineMeshes.push(tube)});
 var leverPivot=new B.TransformNode("lever pivot",scene);leverPivot.position=V(1.28,2.02,0);
 var rod=cylinder("lever",0,.48,0,.065,.96,chrome,leverPivot);var knob=ball("lever knob",0,.98,0,.22,red,leverPivot);
 function clickMesh(o,action){o.actionManager=new B.ActionManager(scene);o.actionManager.registerAction(new B.ExecuteCodeAction(B.ActionManager.OnPickTrigger,action))}
 clickMesh(knob,()=>document.getElementById("lever").click());clickMesh(rod,()=>document.getElementById("lever").click());
 [-.65,0,.65].forEach((x,i)=>{cylinder("button rim",x,2,1.15,.27,.04,chrome);var cap=cylinder("button",x,2.035,1.15,.23,.065,i===2?red:amber);clickMesh(cap,()=>document.getElementById(["down","bet","spin"][i]).click())});
 var carpet=texture("carpet",256,256,(c,w,h)=>{c.fillStyle="#2a080e";c.fillRect(0,0,w,h);c.strokeStyle="#8a6a2c";c.lineWidth=3;c.beginPath();c.moveTo(w/2,10);c.lineTo(w-10,h/2);c.lineTo(w/2,h-10);c.lineTo(10,h/2);c.closePath();c.stroke();c.fillStyle="#0d3236";c.beginPath();c.arc(w/2,h/2,34,0,Math.PI*2);c.fill()});carpet.uScale=carpet.vScale=26;carpet.wrapU=carpet.wrapV=B.Texture.WRAP_ADDRESSMODE;
 var floor=B.MeshBuilder.CreateGround("floor",{width:60,height:60},scene);floor.material=texmat("carpet",carpet,false);
 var displayTex=new B.DynamicTexture("display",{width:1024,height:140},scene,false),display=plane("display",0,1.77,.92,1.94,.22,texmat("display",displayTex,true));
 var coinMaterial=mat("coin","#f4c654",110);
 var lastPaid=0,wasBusy=false,startCoins=0,lastDisplay="",ready=false,frames=0;
 function fit(){engine.resize();var ratio=canvas.clientWidth/Math.max(1,canvas.clientHeight);var r=Math.max(7.8,5.2/Math.max(.55,ratio));cam.lowerRadiusLimit=cam.upperRadiusLimit=r;cam.radius=r}
 window.addEventListener("resize",fit);
 canvas.addEventListener("webglcontextlost",function(e){e.preventDefault();fallback("contexto gráfico perdido")});
 scene.executeWhenReady(function(){if(!engine||engine.isDisposed)return;engine.runRenderLoop(function(){try{
 var st=window.fortunaState(),t=performance.now()/1000;reels.forEach((r,i)=>r.rotation.x=-st.visual[i]*step);lineMeshes.forEach((o,i)=>o.setEnabled(st.wins.some(w=>w.i===i)));
 bulbA.emissiveColor=C("#ffcf6b").scale(.55+Math.max(0,Math.sin(t*(st.last?14:3.2))));bulbB.emissiveColor=C("#ffcf6b").scale(.55+Math.max(0,-Math.sin(t*(st.last?14:3.2))));
 leverPivot.rotation.x=st.busy?-.55:0;
 var text=st.balance+"  |  "+st.cost+"  |  "+st.last;if(text!==lastDisplay){lastDisplay=text;var c=displayTex.getContext();c.fillStyle="#090809";c.fillRect(0,0,1024,140);c.font="bold 84px monospace";c.textAlign="center";c.fillStyle="#ff4632";c.fillText(text,512,100);displayTex.update()}
 if(wasBusy&&!st.busy&&st.last>0){coins.forEach(c=>c.mesh.dispose());coins=[];startCoins=t;for(let i=0;i<Math.min(40,Math.max(6,Math.round(st.last*1.5)));i++){var mesh=cylinder("coin",0,1.58,.94,.13,.024,coinMaterial);mesh.setEnabled(false);coins.push({mesh,delay:i*.05,x:(Math.random()-.5)*.9,z:1.02+Math.random()*.18,angle:Math.random()*5})}}
 coins.forEach(c=>{var a=t-startCoins-c.delay;if(a<0)return;c.mesh.setEnabled(true);var f=Math.min(1,a/.85);c.mesh.position=V(c.x*f,1.32+.26*Math.pow(1-f,2)+Math.abs(Math.sin(f*Math.PI*3))*.11*(1-f),.94+(c.z-.94)*f);c.mesh.rotation.x=c.angle*(1-f)});
 wasBusy=st.busy;scene.render();if(!ready&&++frames>=2){ready=true;document.body.classList.add("real3d");note.textContent="Babylon.js · 3D";fit()}
 }catch(e){fallback(e.message)}});fit()});
 setTimeout(function(){if(!ready)fallback("motor 3D não iniciou")},14000);
 }catch(e){fallback(e.message)}
};
})();
