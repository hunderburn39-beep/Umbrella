const { chromium, webkit }=require("playwright");
const assert=require("node:assert/strict");
const fs=require("node:fs");
(async()=>{
 const dir=process.env.RUNNER_TEMP||".";
 const browserName=process.env.BROWSER||"chromium";
 const browser=await (browserName==="webkit"?webkit:chromium).launch(browserName==="webkit"?{headless:true}:{headless:true,args:["--use-angle=swiftshader","--enable-unsafe-swiftshader"]});
 try{
  for(const [width,height] of [[844,390],[390,844]]){
   const page=await browser.newPage({viewport:{width,height},isMobile:true,hasTouch:true,deviceScaleFactor:1});
   const errors=[];page.on("pageerror",e=>errors.push(e.message));
   try{
    await page.goto("http://127.0.0.1:8765/Fortuna-777-V8/",{waitUntil:"domcontentloaded"});
    await page.waitForFunction(()=>window.fortuna3DReady===true,{},{timeout:45000});
    await page.screenshot({path:dir+"/fortuna-"+browserName+"-"+width+"-ready.png"});
    assert.equal(await page.locator("#scene3d").isVisible(),true);
    const initial=await page.evaluate(()=>window.fortunaState());
    await page.locator("#refill").tap();
    assert.equal((await page.evaluate(()=>window.fortunaState())).balance,initial.balance+100);
    const before=await page.evaluate(()=>window.fortunaState());
    await page.locator("#spin").tap();
    await page.waitForFunction(()=>window.fortunaState().busy);
    await page.waitForFunction(()=>!window.fortunaState().busy,{},{timeout:10000});
    const after=await page.evaluate(()=>window.fortunaState());
    assert.equal(after.balance,before.balance-before.cost+after.last);
    assert.deepEqual(after.visual,after.stops);
    assert.equal(await page.evaluate(()=>window.fortuna3DReady),true);
    assert.equal(errors.length,0,errors.join("\n"));
    await page.screenshot({path:dir+"/fortuna-"+browserName+"-"+width+"-round.png"});
    console.log("PASS",browserName,width,height,after);
   }catch(e){await page.screenshot({path:dir+"/fortuna-"+browserName+"-"+width+"-failed.png"});console.log(await page.locator("#engineNote").textContent());throw e}
   finally{await page.close()}
  }
 }finally{await browser.close()}
})().catch(e=>{console.error(e);process.exitCode=1});
