// Visit each preset place and screenshot (real data). node test_places.js OUTDIR PORT [w h]
const { chromium } = require(process.env.PW || 'playwright');
const path = require('path');
const [,, OUT, PORT, W, H] = process.argv;
const THREE_DIR = path.join(__dirname, '..', 'npm', 'three-0.169.0', 'package');
(async () => {
  const browser = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium', args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
  const ctx = await browser.newContext({ viewport: { width: +(W || 1100), height: +(H || 680) } });
  const page = await ctx.newPage();
  const logs = [];
  page.on('console', m => { if (['error', 'warning'].includes(m.type())) logs.push(m.type() + ': ' + m.text()); });
  page.on('pageerror', e => logs.push('pageerror: ' + e));
  await page.route(/cdn\.jsdelivr\.net\/npm\/three@0\.169\.0\/(.*)/, r => { const m = r.request().url().match(/three@0\.169\.0\/(.*)$/); r.fulfill({ path: path.join(THREE_DIR, m[1]), contentType: 'application/javascript' }); });
  await page.route(/fonts\.(googleapis|gstatic)\.com/, r => r.abort());
  await page.addInitScript(() => { window.claude = { use: async () => null }; });
  const t0 = Date.now();
  await page.goto('http://127.0.0.1:' + PORT + '/index.html', { waitUntil: 'load' });
  await page.waitForFunction(() => document.getElementById('loader').hidden, null, { timeout: 300000 });
  console.log('loaded in', (Date.now() - t0) / 1000, 's');
  await page.click('#collapse');
  const settle = async (ms) => { await page.waitForTimeout(ms); };
  await settle(5000);
  await page.screenshot({ path: path.join(OUT, 'p_start.png'), timeout: 180000 });
  const names = await page.$$eval('#places .chip', (bs) => bs.map((b) => b.textContent));
  const only = process.env.ONLY ? process.env.ONLY.split(',') : null;
  for (let i = 0; i < names.length; i++) {
    if (only && !only.includes(String(i))) continue;
    await page.evaluate((i) => document.querySelectorAll('#places .chip')[i].click(), i);
    await settle(6000);
    await page.screenshot({ path: path.join(OUT, 'p_' + i + '.png'), timeout: 180000 });
    console.log('place', i, names[i]);
  }
  if (process.env.COMPARE) {
    await page.evaluate(() => { document.getElementById('t-plan').click(); document.querySelector('[data-opt=garden] [data-v=today]').click(); document.getElementById('t-fence').click(); });
    await settle(6000);
    await page.screenshot({ path: path.join(OUT, 'p_today.png'), timeout: 180000 });
  }
  console.log('logs:\n' + logs.slice(0, 30).join('\n'));
  await browser.close();
})();
