// usage: node record.js <seed> [answer] [record]   (env: GAME_URL, LEVEL=Easy|Normal|Hard)
// Plays a seeded vs-bot match on the English A-Z board. With 'record', saves 1080x1920 frames to ./frames.
const { chromium } = require('playwright');
const [seed, answer, record] = [Number(process.argv[2]||1), process.argv[3], process.argv[4]==='record'];
const ORDER = 'EARIOTNSLCUDPMHGBFYWKVXZJQ'.split('');
(async () => {
  const b = await chromium.launch();
  const ctx = await b.newContext({ viewport:{width:432,height:768}, deviceScaleFactor:2.5,
    });
  await ctx.addInitScript(s => { let a=s; Math.random=()=>{a|=0;a=a+0x6D2B79F5|0;let t=Math.imul(a^a>>>15,1|a);t=t+Math.imul(t^t>>>7,61|t)^t;return((t^t>>>14)>>>0)/4294967296;}; }, seed);
  const p = await ctx.newPage(); const T0=Date.now(); const mark=(n)=>console.log('MARK',n,((Date.now()-T0)/1000).toFixed(2));
  const fs=require('fs'); const frames=[]; let shooting=false, loop;
  const startCapture = () => {
  if (record) { fs.rmSync('frames',{recursive:true,force:true}); fs.mkdirSync('frames'); shooting=true;
    loop=(async()=>{ while(shooting){ const t=(Date.now()-T0)/1000; try{ const buf=await p.screenshot({type:'jpeg',quality:90,timeout:3000}); const i=frames.length; frames.push(t); fs.writeFileSync(`frames/${String(i).padStart(5,'0')}.jpg`,buf);}catch(e){} } })(); }
  };
  const f = encodeURIComponent(JSON.stringify({language:'en',categories:[],length:{min:5,max:7}}));
  await p.goto((process.env.GAME_URL||'http://localhost:8082/en/bot')+'?filters='+f); await p.waitForTimeout(2500);
  // capture only after the page has loaded: a screenshot taken during navigation can hang
  startCapture();
  await p.getByText('Skip',{exact:true}).click(); await p.waitForTimeout(400);
  await p.getByText(process.env.LEVEL||'Hard',{exact:true}).click(); mark('board'); await p.waitForTimeout(1500);
  // exact game-over time: a MutationObserver in the page stamps Date.now() the moment "got it!" appears
  // (textContent, not innerText: innerText forces layout on every mutation and stalls the screenshots)
  await p.evaluate(() => { const ob = new MutationObserver(() => {
      if (document.body.textContent.includes(' got it!')) { window.__overAt = Date.now(); ob.disconnect(); } });
    ob.observe(document.body, { subtree: true, childList: true, characterData: true }); });
  const t0 = Date.now(); let myTurns = 0, idx = 0;
  const body = () => p.innerText('body');
  while (Date.now()-t0 < 120000) {
    const txt = await body();
    if (/You win|wins|Draw|draw|Rematch|Play again/.test(txt) && !/Right answer wins/.test(txt)) break;
    const sub = p.getByText('Submit',{exact:true});
    const myAnswer = /Turn\s*\n?\s*You/.test(txt) && await sub.isVisible().catch(()=>false);
    if (myAnswer) {
      myTurns++;
      if (answer && myTurns >= 4) {
        await p.getByPlaceholder(/Type the English word/).pressSequentially(answer, {delay:120});
        await p.waitForTimeout(400); await sub.click(); await p.waitForTimeout(2500); continue;
      }
      await p.waitForTimeout(500);
      await p.getByText('Pass',{exact:true}).click(); await p.waitForTimeout(700);
      // open a cell
      for (; idx < ORDER.length; idx++) {
        const before = await body();
        await p.getByText(ORDER[idx],{exact:true}).first().click({timeout:2000}).catch(()=>{});
        await p.waitForTimeout(600);
        if ((await body()) !== before) { mark('open_'+ORDER[idx]); idx++; break; }
      }
    }
    await p.waitForTimeout(400);
  }
  mark('over'); const overAt = await p.evaluate(() => window.__overAt || 0);
  if (overAt) console.log('MARK over_exact', ((overAt - T0) / 1000).toFixed(2));
  await p.waitForTimeout(2500);
  await p.screenshot({path:`shots/end-${seed}.png`});
  console.log((await body()).slice(0,700).replace(/\n/g,' | '));
  if (record) { shooting=false; await loop; fs.writeFileSync('frames/times.json', JSON.stringify(frames));
    if (frames.length < 100) { console.error(`only ${frames.length} frames captured`); process.exitCode = 3; } }
  await ctx.close(); await b.close();
})();
