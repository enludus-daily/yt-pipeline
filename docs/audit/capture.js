// usage: node docs/audit/capture.js <url> <out.png|out.pdf>
// Full-page capture at 1280px wide with the page URL shown in a bar at the top.
const { chromium } = require('playwright');
const [url, out] = process.argv.slice(2);
(async () => {
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 1280, height: 900 } });
  await p.goto(url, { waitUntil: 'networkidle' });
  await p.evaluate((u) => {
    const bar = document.createElement('div');
    bar.textContent = '🔒 ' + u;
    bar.style.cssText = 'position:relative;z-index:9999;background:#e8eaed;color:#202124;font:15px Arial,sans-serif;padding:10px 16px;border-bottom:1px solid #c4c7cc';
    document.body.prepend(bar);
  }, url);
  await p.waitForTimeout(500);
  if (out.endsWith('.pdf')) await p.pdf({ path: out, format: 'A4', printBackground: true });
  else await p.screenshot({ path: out, fullPage: true });
  await b.close();
})();
