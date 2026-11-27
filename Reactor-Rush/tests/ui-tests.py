#!/usr/bin/env python3
"""Testes de interface (Chrome headless via Playwright). Safari/iPhone NÃO são testáveis neste ambiente."""
import asyncio, json, sys, os
from playwright.async_api import async_playwright
HERE=os.path.dirname(os.path.abspath(__file__)); SHOTS=os.environ.get('RR_SHOTS',HERE+'/shots'); os.makedirs(SHOTS,exist_ok=True)
URL='file://'+os.path.dirname(HERE)+'/index.html?rrtest=1'
res=[]
def rec(name,ok,detail=''): res.append({'test':name,'ok':bool(ok),'detail':str(detail)}); print('PASS' if ok else 'FAIL',name,'—',detail)
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(executable_path='/usr/bin/google-chrome',args=['--no-sandbox'])
        pg=await b.new_page(viewport={'width':844,'height':390})
        errs=[]
        pg.on('pageerror',lambda e:errs.append('PAGEERR '+str(e)))
        pg.on('console',lambda m:errs.append('CONSOLE '+m.text) if m.type=='error' else None)
        await pg.goto(URL); await pg.wait_for_timeout(1500)
        rec('Carrega com 49 células',await pg.evaluate("document.querySelectorAll('#grid .cell').length")==49)
        # geometria
        g=await pg.evaluate("(()=>{const r=document.getElementById('grid').getBoundingClientRect(),a=document.getElementById('arena').getBoundingClientRect(),c=document.querySelector('#grid .cell');return [r.width,r.height,a.width,a.height,c?getComputedStyle(c).backgroundSize:'']})()")
        rec('Grelha preenche a moldura (horizontal)',abs(g[0]-g[2])<=1.5 and abs(g[1]-g[3])<=1.5 and 0.8<=g[0]/g[1]<=1.2 and g[4]=='contain',g)
        circ=await pg.evaluate("""[...document.querySelectorAll('#spin,#info,#sound,#menu,#minus,#plus')].map(e=>[e.id,e.offsetWidth,e.offsetHeight]).filter(x=>x[1]>0)""")
        rec('Botões circulares com largura=altura',all(abs(w-h)<=1.5 for _,w,h in circ),circ)
        # mensagens
        keys=await pg.evaluate("window.__rr.keys")
        rec('11 mensagens definidas',len(keys)==11,keys)
        for k in keys:
            await pg.evaluate("k=>window.__rr.banner(k,k.includes('WIN')?123.45:0,false)",k)
            await pg.wait_for_timeout(900)
            info=await pg.evaluate("""(()=>{const e=document.querySelector('.rr3d');if(!e)return null;const cs=getComputedStyle(e);const r=e.getBoundingClientRect();const a=document.getElementById('grid').getBoundingClientRect();return {bg:cs.backgroundColor,bw:cs.borderTopWidth,sh:cs.boxShadow,txt:e.textContent,w:r.width,gw:a.width}})()""")
            ok=info and info['bg'] in('rgba(0, 0, 0, 0)','transparent') and info['bw']=='0px' and info['sh']=='none' and info['w']<=info['gw']*1.02
            rec('Mensagem '+k+' sem caixa e dentro da grelha',ok,info and (info['txt'][:30],round(info['w']),round(info['gw'])))
            if k in('GARGANTOON UNLEASHED','MAX WIN','QUANTUM OVERLOAD'): await pg.screenshot(path=SHOTS+'/banner_'+k.replace(' ','_')+'.png')
            await pg.wait_for_timeout(1800)
        # repetição determinística: mesma semente -> o saldo final da interface = resultado do motor
        for seed in (3333,555555,1,5,19,20,104,171,454,668,316,499):
            r=await pg.evaluate("""async (seed)=>{const R=window.__rr,E=R.E;const bet=R.betNow();const g0=Object.assign({},R.gov());const exp=E.playGovernedRound(E.createRng(seed),g0,bet,E.DEFAULTS,true);
              R.setSeed(seed);const b0=R.state().balance;await R.spin();const b1=R.state().balance;return {exp:Math.round(exp.win*bet*100)/100,got:Math.round((b1-b0+bet)*100)/100,casc:exp.cascades}}""",seed)
            rec('Repetição determinística semente '+str(seed)+' (motor = interface)',abs(r['exp']-r['got'])<0.011,r)
        # tiers
        tiers=await pg.evaluate("[[9.9,0],[10,0],[20,0],[50,0],[100,0],[250,0],[1000,0]].map(x=>window.__rr.winTier(x[0]))")
        rec('Patamares 10/20/50/100/250/1000',tiers==[None,'BIG WIN','MEGA WIN','SUPER WIN','EPIC WIN','QUANTUM WIN','MAX WIN'],tiers)
        # tabela de prémios no menu
        await pg.click('#info'); await pg.wait_for_timeout(300)
        rows=await pg.evaluate("document.querySelectorAll('#payTable tr').length")
        uses=await pg.evaluate("document.querySelectorAll('#payTable use').length")
        rec('Menu de informações: tabela com 8 símbolos',rows==9 and uses==8,(rows,uses))
        await pg.screenshot(path=SHOTS+'/help.png'); await pg.evaluate("document.getElementById('help').hidden=true")
        # jogo: 60 rondas turbo, conservação de saldo, desempenho
        await pg.evaluate("""window.__lt=0;new PerformanceObserver(l=>{for(const e of l.getEntries())window.__lt=Math.max(window.__lt,e.duration)}).observe({entryTypes:['longtask']})""")
        await pg.click('#turbo'); bal0=await pg.evaluate("window.__rr.state().balance"); spins=0
        for i in range(60):
            await pg.click('#spin',force=True)
            await pg.wait_for_function("!document.getElementById('spin').classList.contains('active')",timeout=90000); spins+=1
        st=await pg.evaluate("window.__rr.state()")
        rec('60 rondas sem erros JS',not errs,errs[:3]); rec('Contador de rondas',st['spins']>=60,st['spins'])
        rec('Saldo válido e finito',isinstance(st['balance'],(int,float)) and st['balance']>=0,st['balance'])
        gv=await pg.evaluate("(()=>{const g=window.__rr.gov();return {bets:g.bets,paid:g.paid,cap:g.rtpCap,rounds:g.rounds}})()")
        rec('Reserva da casa: total pago <= 94% do apostado',gv['rounds']>=60 and gv['paid']<=gv['cap']*gv['bets']+1e-9,gv)
        lt=await pg.evaluate("window.__lt"); rec('Maior long task < 400 ms (Chrome headless)',lt<400,round(lt))
        # orientação
        await pg.set_viewport_size({'width':390,'height':844}); await pg.wait_for_timeout(800); await pg.screenshot(path=SHOTS+'/portrait.png')
        g2=await pg.evaluate("(()=>{const r=document.getElementById('grid').getBoundingClientRect(),a=document.getElementById('arena').getBoundingClientRect(),c=document.querySelector('#grid .cell');return [r.width,r.height,a.width,a.height,c?getComputedStyle(c).backgroundSize:'']})()")
        rec('Retrato: grelha preenche a moldura ou aviso de rotação',(g2[0]>0 and abs(g2[0]-g2[2])<=1.5 and abs(g2[1]-g2[3])<=1.5 and 0.8<=g2[0]/g2[1]<=1.2 and g2[4]=='contain') or g2[0]==0,g2)
        await pg.set_viewport_size({'width':844,'height':390}); await pg.wait_for_timeout(800)
        g3=await pg.evaluate("(()=>{const r=document.getElementById('grid').getBoundingClientRect(),a=document.getElementById('arena').getBoundingClientRect(),c=document.querySelector('#grid .cell');return [r.width,r.height,a.width,a.height,c?getComputedStyle(c).backgroundSize:'']})()")
        rec('Regresso a horizontal: grelha preenche a moldura',abs(g3[0]-g3[2])<=1.5 and abs(g3[1]-g3[3])<=1.5 and 0.8<=g3[0]/g3[1]<=1.2 and g3[4]=='contain',g3)
        await pg.set_viewport_size({'width':1280,'height':720}); await pg.wait_for_timeout(600)
        g4=await pg.evaluate("(()=>{const r=document.getElementById('grid').getBoundingClientRect(),a=document.getElementById('arena').getBoundingClientRect(),c=document.querySelector('#grid .cell');return [r.width,r.height,a.width,a.height,c?getComputedStyle(c).backgroundSize:'']})()")
        rec('16:9 desktop: grelha preenche a moldura',abs(g4[0]-g4[2])<=1.5 and abs(g4[1]-g4[3])<=1.5 and 0.8<=g4[0]/g4[1]<=1.2 and g4[4]=='contain',g4)
        art=await pg.evaluate("[document.querySelectorAll('#rrP1 .rq-bg svg').length,document.querySelectorAll('#rrTubes .tube .rq-core').length,document.querySelectorAll('#rrP2 .rq-bg svg').length,document.querySelectorAll('#rrReactors .rq-pod').length,!!document.querySelector('#rrP2 .rq-portal')]")
        rec('Arte animada dos reatores presente (Quantumeter e Fluctometer)',art==[1,4,1,4,True],art)
        # demo Gargantoon
        await pg.set_viewport_size({'width':844,'height':390}); await pg.wait_for_timeout(500)
        bal=await pg.evaluate("window.__rr.state().balance")
        await pg.evaluate("window.__rr.demoGargantoon()"); await pg.wait_for_function("!document.getElementById('spin').classList.contains('active')&&!document.querySelector('.rr3d')",timeout=120000)
        bal2=await pg.evaluate("window.__rr.state().balance")
        rec('Demo Gargantoon não altera saldo e sem erros',bal==bal2 and not errs,(bal,bal2,errs[:2]))
        await b.close()
    json.dump(res,open(HERE+'/results-ui.json','w'),indent=1,ensure_ascii=False)
    bad=[r for r in res if not r['ok']]; print(len(res)-len(bad),'/',len(res),'passaram'); sys.exit(1 if bad else 0)
asyncio.run(main())
