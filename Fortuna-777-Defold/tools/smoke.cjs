const { chromium } = require("playwright");
const assert = require("node:assert/strict");
(async () => {
  const browser = await chromium.launch({headless:true,args:["--use-angle=swiftshader","--enable-unsafe-swiftshader"]});
  try {
    const page = await browser.newPage({viewport:{width:960,height:600},hasTouch:true,isMobile:true});
    const logs=[], errors=[];
    page.on("console",m=>{logs.push(m.text());console.log(m.text());});
    page.on("pageerror",e=>errors.push(e.message));
    page.on("response",r=>{if(r.status()>=400 && /localhost|127\.0\.0\.1/.test(r.url())) errors.push(r.status()+" "+r.url());});
    const waitLog=async (needle,timeout=45000)=>{
      const end=Date.now()+timeout;
      while(!logs.some(s=>s.includes(needle))) {
        if(errors.length) throw Error(errors.join("\n"));
        if(Date.now()>end) throw Error("Missing log: "+needle);
        await page.waitForTimeout(250);
      }
    };
    await page.goto("http://127.0.0.1:8765/",{waitUntil:"load"});
    await waitLog("FORTUNA_READY");
    const canvas=page.locator("#canvas");
    const rect=await canvas.boundingBox();
    assert(rect && rect.width>0 && rect.height>0,"Canvas not visible");
    await page.screenshot({path:process.env.RUNNER_TEMP+"/fortuna-ready.png"});
    await page.touchscreen.tap(rect.x+rect.width*680/960,rect.y+rect.height*485/540);
    await waitLog("FORTUNA_ROUND_DONE",15000);
    assert.equal(errors.length,0,errors.join("\n"));
    await page.screenshot({path:process.env.RUNNER_TEMP+"/fortuna-round.png"});
    console.log("PASS: Defold WebAssembly loaded and completed a touch round");
  } finally { await browser.close(); }
})().catch(e=>{console.error(e);process.exitCode=1;});
