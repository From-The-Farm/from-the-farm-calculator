// Local functional check of the walk-through viewer with a mocked window.claude (db).
const { chromium } = require(process.env.PW || 'playwright');
const path = require('path');
const [,, OUT, PORT] = process.argv;
const THREE_DIR = path.join(__dirname, '..', 'npm', 'three-0.169.0', 'package');
(async () => {
  const browser = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium', args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
  const ctx = await browser.newContext({ viewport: { width: 1280, height: 800 } });
  const page = await ctx.newPage();
  const logs = [];
  page.on('console', m => { if (['error', 'warning'].includes(m.type())) logs.push(m.type() + ': ' + m.text()); });
  page.on('pageerror', e => logs.push('pageerror: ' + e));
  await page.route(/cdn\.jsdelivr\.net\/npm\/three@0\.169\.0\/(.*)/, r => {
    const m = r.request().url().match(/three@0\.169\.0\/(.*)$/);
    r.fulfill({ path: path.join(THREE_DIR, m[1]), contentType: 'application/javascript' });
  });
  await page.route(/fonts\.(googleapis|gstatic)\.com/, r => r.abort());
  await page.addInitScript(() => {
    const store = new Map(); const subs = [];
    const snapOf = (c) => { const docs = [...store.keys()].filter(k => k.startsWith(c + '/') && k.split('/').length === c.split('/').length + 1).sort().map(k => ({ id: k.split('/').pop(), exists: true, data: () => store.get(k), metadata: {} })); return { docs, size: docs.length, empty: !docs.length, docChanges: () => [] }; };
    const notify = () => subs.forEach(s => s.next(snapOf(s.c)));
    const docRef = (p) => ({ id: p.split('/').pop(), path: p, get: async () => ({ id: p.split('/').pop(), exists: store.has(p), data: () => store.get(p) }),
      set: async (d) => { store.set(p, JSON.parse(JSON.stringify(d))); setTimeout(notify, 10); }, update: async (d) => { store.set(p, Object.assign({}, store.get(p), d)); setTimeout(notify, 10); }, delete: async () => { store.delete(p); setTimeout(notify, 10); } });
    const db = { doc: docRef, collection: (c) => ({ path: c, doc: (id) => docRef(c + '/' + id), get: async () => snapOf(c), onSnapshot: (next, err) => { const s = { c, next }; subs.push(s); setTimeout(() => next(snapOf(c)), 20); return () => {}; } }) };
    window.__store = store;
    window.claude = { use: async (n) => n === 'db' ? db : null };
  });
  await page.goto('http://127.0.0.1:' + PORT + '/index.html', { waitUntil: 'load' });
  try { await page.waitForFunction(() => document.getElementById('loader').hidden, null, { timeout: 180000 }); } catch (e) { logs.push('loader not hidden: ' + await page.evaluate(() => document.getElementById('load-text').textContent)); }
  await page.waitForTimeout(2500);
  await page.screenshot({ path: path.join(OUT, 'v_walk.png'), timeout: 180000 });
  await page.click('button[data-mode="top"]');
  await page.waitForTimeout(2500);
  await page.screenshot({ path: path.join(OUT, 'v_top.png'), timeout: 180000 });
  // draw a path
  await page.click('button[data-draw="path"]');
  for (const [x, y] of [[420, 380], [520, 420], [600, 470], [640, 560]]) { await page.mouse.click(x, y); await page.waitForTimeout(150); }
  await page.click('#d-finish');
  await page.fill('#f-note', 'Test path from the deck to the office');
  await page.click('#f-save');
  await page.waitForTimeout(800);
  await page.click('button[data-draw="area"]');
  for (const [x, y] of [[300, 300], [380, 300], [380, 360], [300, 360]]) { await page.mouse.click(x, y); await page.waitForTimeout(120); }
  await page.keyboard.press('Enter');
  await page.selectOption('#f-mat', 'turf');
  await page.click('#f-save');
  await page.waitForTimeout(1200);
  await page.screenshot({ path: path.join(OUT, 'v_marks.png'), timeout: 180000 });
  const store = await page.evaluate(() => JSON.stringify([...window.__store.entries()]));
  console.log('store', store.slice(0, 600));
  await page.click('button[data-mode="orbit"]');
  await page.waitForTimeout(2500);
  await page.screenshot({ path: path.join(OUT, 'v_orbit.png'), timeout: 180000 });
  await page.setViewportSize({ width: 390, height: 844 });
  await page.waitForTimeout(2500);
  await page.screenshot({ path: path.join(OUT, 'v_phone.png'), timeout: 180000 });
  console.log('phone overflow', await page.evaluate(() => [document.documentElement.scrollWidth, innerWidth]));
  console.log('logs:\n' + logs.slice(0, 30).join('\n'));
  await browser.close();
})();
