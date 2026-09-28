// Local functional check of the upload page with a mocked window.claude (db + assets).
const { chromium } = require(process.env.PW || 'playwright');
const path = require('path');
const fs = require('fs');
const [,, VIDEO, OUT, MAXBYTES] = process.argv;
const MP4BOX = path.join(__dirname, '..', 'npm', 'mp4box-0.5.4', 'package', 'dist', 'mp4box.all.min.js');
(async () => {
  const browser = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium' });
  const ctx = await browser.newContext({ viewport: { width: 1280, height: 900 } });
  const page = await ctx.newPage();
  const logs = [];
  page.on('console', m => logs.push(m.type() + ': ' + m.text()));
  page.on('pageerror', e => logs.push('pageerror: ' + e));
  await page.route(/cdn\.jsdelivr\.net\/npm\/mp4box@0\.5\.4\/dist\/mp4box\.all\.min\.js/, r => r.fulfill({ path: MP4BOX, contentType: 'application/javascript' }));
  await page.route(/fonts\.(googleapis|gstatic)\.com/, r => r.abort());
  await page.addInitScript((maxBytes) => {
    const store = new Map();
    const uploads = [];
    window.__store = store; window.__uploads = uploads;
    const snap = (p) => ({ id: p.split('/').pop(), exists: store.has(p), data: () => store.get(p), metadata: { fromCache: false, hasPendingWrites: false } });
    const docRef = (p) => ({ id: p.split('/').pop(), path: p,
      get: async () => snap(p),
      set: async (d) => { await new Promise(r => setTimeout(r, 5)); store.set(p, JSON.parse(JSON.stringify(d))); },
      update: async (d) => { store.set(p, Object.assign({}, store.get(p), d)); },
      delete: async () => { store.delete(p); } });
    const db = {
      doc: docRef,
      collection: (c) => ({ path: c, doc: (id) => docRef(c + '/' + id),
        get: async () => { const docs = [...store.keys()].filter(k => k.startsWith(c + '/') && k.split('/').length === c.split('/').length + 1).sort().map(snap); return { docs, size: docs.length, empty: !docs.length }; } }) };
    let bytes = 0, n = 0;
    const assets = {
      upload: async (blob, opts) => {
        await new Promise(r => setTimeout(r, 30));
        if (bytes + blob.size > maxBytes) { const e = new Error('quota'); e.code = 'quota_or_state'; throw e; }
        n++; bytes += blob.size;
        const id = String(n).padStart(32, '0');
        const buf = new Uint8Array(await blob.arrayBuffer());
        uploads.push({ id, size: blob.size, type: opts && opts.type, keep: (n <= 2) ? buf : null });
        return { id, url: '/_blob/' + id, sizeBytes: blob.size, contentType: 'image/jpeg' };
      },
      list: async () => ({ assets: [], usage: { files: n, bytes, maxFiles: 1000, maxBytes } }),
      delete: async () => ({ deleted: false }) };
    window.claude = { use: async (name) => { await new Promise(r => setTimeout(r, 50)); return name === 'db' ? db : name === 'assets' ? assets : null; } };
  }, Number(MAXBYTES || 2e9));
  await page.goto('http://127.0.0.1:8766/index.html', { waitUntil: 'load' });
  await page.waitForTimeout(400);
  const sup = await page.evaluate(async () => {
    const r = {};
    for (const c of ['avc1.640028', 'vp09.00.10.08', 'hvc1.1.6.L120.90']) { try { r[c] = (await VideoDecoder.isConfigSupported({ codec: c, codedWidth: 1920, codedHeight: 1080 })).supported; } catch (e) { r[c] = 'err ' + e.message; } }
    r.DataStream = typeof DataStream; r.MP4Box = typeof MP4Box;
    const v = document.createElement('video'); r.h264el = v.canPlayType('video/mp4; codecs="avc1.640028"'); r.vp9el = v.canPlayType('video/mp4; codecs="vp09.00.10.08"');
    return r; });
  console.log('support', JSON.stringify(sup));
  await page.screenshot({ path: path.join(OUT, 'up_idle.png'), fullPage: true });
  const t0 = Date.now();
  await page.setInputFiles('#file', VIDEO);
  let last = '';
  for (let i = 0; i < 600; i++) {
    await page.waitForTimeout(1000);
    const st = await page.evaluate(() => document.getElementById('status').textContent + ' | ' + document.getElementById('f-sent').textContent);
    if (st !== last) { console.log(((Date.now() - t0) / 1000).toFixed(1) + 's', st); last = st; }
    if (/All \d+ frames|Something went wrong|can't read|storage is full|Paused/.test(st)) break;
  }
  await page.screenshot({ path: path.join(OUT, 'up_done.png'), fullPage: true });
  const res = await page.evaluate(() => {
    const out = { docs: {}, uploads: window.__uploads.map(u => ({ id: u.id, size: u.size, type: u.type })) };
    for (const [k, v] of window.__store) out.docs[k] = v;
    out.sheets = window.__uploads.filter(u => u.keep).map(u => { let s = ''; const b = u.keep; for (let i = 0; i < b.length; i += 0x8000) s += String.fromCharCode.apply(null, b.subarray(i, i + 0x8000)); return btoa(s); });
    return out; });
  res.sheets.forEach((b, i) => fs.writeFileSync(path.join(OUT, 'sheet' + i + '.jpg'), Buffer.from(b, 'base64')));
  delete res.sheets;
  fs.writeFileSync(path.join(OUT, 'result.json'), JSON.stringify(res, null, 1));
  const cur = res.docs['upload/current'];
  console.log('current', JSON.stringify(cur));
  console.log('uploads', res.uploads.length, 'bytes', res.uploads.reduce((a, u) => a + u.size, 0));
  const pages = Object.keys(res.docs).filter(k => k.includes('/pages/'));
  console.log('pages', pages, pages.map(p => res.docs[p].items.length));
  console.log('logs', logs.slice(0, 20).join('\n'));
  await browser.close();
})();
