#!/usr/bin/env node
/**
 * Resumable headless-scraper skeleton.
 * Fill in: UNIVERSE shape, routeFor(), ASSET_OK(), extract().
 * Run with: TMPDIR=/tmp OUT_DIR=/path node resumable-scraper.mjs [--limit N] [--only a,b] [--retry-nulls]
 *
 * Contract: one item = one page load; every result written immediately (atomic JSON +
 * append-only JSONL); null is a completed record; never throw out of the item loop.
 */
import fs from 'fs';
import path from 'path';
import { chromium } from 'playwright-core';

const EXE = process.env.CHROME_PATH || '/opt/data/scrapling-browsers/chromium-1243/chrome-linux64/chrome';
const OUT_DIR = process.env.OUT_DIR || '/opt/data/hl-blurbs';
const UNIVERSE = process.env.UNIVERSE || path.join(OUT_DIR, 'scraper', 'universe.json');
const STATE = path.join(OUT_DIR, 'hl_all_blurbs.json');
const JSONL = path.join(OUT_DIR, 'blurbs.jsonl');
const PROGRESS = path.join(OUT_DIR, 'progress.log');
const DONE = path.join(OUT_DIR, 'DONE.txt');
const TMP = path.join(OUT_DIR, 'tmp');
fs.mkdirSync(TMP, { recursive: true });

const argv = process.argv.slice(2);
const arg = (n, d) => { const i = argv.indexOf(n); return i >= 0 ? argv[i + 1] : d; };
const LIMIT = parseInt(arg('--limit', '0'), 10) || 0;
const ONLY = arg('--only', '');
const RETRY_NULLS = argv.includes('--retry-nulls');
const sleep = ms => new Promise(r => setTimeout(r, ms));
const nowISO = () => new Date().toISOString();
const log = (...a) => console.log(`[${nowISO().slice(11, 19)}]`, ...a);

function atomicWrite(file, data) {
  const t = path.join(TMP, path.basename(file) + '.new');
  fs.writeFileSync(t, data);
  fs.renameSync(t, file); // same filesystem => atomic
}

// ---------- state (resume) ----------
let results = {};
if (fs.existsSync(STATE)) { try { results = JSON.parse(fs.readFileSync(STATE, 'utf8')); } catch { results = {}; } }
if (!Object.keys(results).length && fs.existsSync(JSONL)) {
  for (const line of fs.readFileSync(JSONL, 'utf8').split('\n')) {
    if (!line.trim()) continue;
    try { const o = JSON.parse(line); results[o.key] = o.val; } catch {}
  }
}

const universe = JSON.parse(fs.readFileSync(UNIVERSE, 'utf8'));
let todo = ONLY ? universe.filter(u => ONLY.split(',').includes(u.coin)) : universe.slice();
if (RETRY_NULLS) todo = todo.filter(u => u.coin in results && results[u.coin].blurb == null);
else todo = todo.filter(u => !(u.coin in results));
if (LIMIT) todo = todo.slice(0, LIMIT);
const total = universe.length;
log(`universe=${total} pending=${todo.length} done=${Object.keys(results).length}`);

// ---------- browser ----------
const args = ['--no-sandbox', '--disable-dev-shm-usage', '--disable-gpu',
  '--disable-background-timer-throttling', '--disable-renderer-backgrounding'];
let browser, page;
async function launch() {
  browser = await chromium.launch({ executablePath: EXE, headless: true, args });
  const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 }, locale: 'en-US', timezoneId: 'UTC' });
  page = await ctx.newPage();
  page.setDefaultTimeout(45000);
}
const recycle = async () => { try { await browser?.close(); } catch {} await launch(); };

// ---------- site-specific (EDIT THESE) ----------
const routeFor = item => item.route;                       // e.g. 'BTC' | 'xyz:GOOGL' | 'QQQ/USDC'
const TITLE_JS = `(() => {
  for (const el of document.querySelectorAll('body *')) {
    const t = (el.textContent || '').trim();
    if (el.children.length === 0 && t.length < 30 && /^[A-Z0-9._:]+[\\/-][A-Z0-9]+$/i.test(t)) {
      const r = el.getBoundingClientRect();
      if (r.width > 0 && r.top < 320 && r.left < 420) return { txt: t, x: r.x, y: r.y, w: r.width, h: r.height };
    }
  }
  return null;
})()`;
const ICON_JS = `(() => {
  const im = document.querySelector('img[src^="/coins/"]');
  if (!im) return null;
  const r = im.getBoundingClientRect();
  return r.width > 5 ? { x: r.x + r.width / 2, y: r.y + r.height / 2, src: im.getAttribute('src') } : null;
})()`;
const MODAL_JS = `(() => {
  const bad = ['Order Book', 'Buy / Long', 'Spread', 'Available to Trade', 'Announcements'];
  let best = null;
  for (const el of document.querySelectorAll('div.modal')) {
    const t = (el.innerText || '').trim();
    if (t.length < 60 || t.length > 1600 || bad.some(b => t.includes(b))) continue;
    const r = el.getBoundingClientRect();
    if (r.width < 220 || r.width > 900) continue;
    if (!best || t.length < best.txt.length) best = { txt: t, desc: (el.querySelector('div[style*="pre-wrap"]') || {}).innerText || null };
  }
  return best;
})()`;

async function scrapeOne(item) {
  try { await page.keyboard.press('Escape'); } catch {}
  await page.goto(`https://app.hyperliquid.xyz/trade/${routeFor(item)}`, { waitUntil: 'domcontentloaded', timeout: 60000 });

  let title = null;
  for (let i = 0; i < 22 && !title; i++) { title = await page.evaluate(TITLE_JS); if (!title) await sleep(800); }
  if (!title) return { blurb: null, note: 'no-title' };

  // identity by machine id, NOT display name
  const icon = await page.evaluate(ICON_JS);
  const ok = icon?.src ? decodeURIComponent(icon.src).includes(String(item.route)) : true;
  if (!ok) return { blurb: null, note: `wrong-page:${title.txt}` };

  await sleep(9000 + Math.floor(Math.random() * 3000));
  const read = async () => {
    for (let i = 0; i < 7; i++) {
      const m = await page.evaluate(MODAL_JS);
      if (m) return { blurb: m.desc || m.txt.split('\n').slice(1).join('\n') || null, note: 'ok' };
      await sleep(700);
    }
    return null;
  };
  if (icon) { await page.mouse.click(icon.x, icon.y); const r = await read(); if (r) return r; try { await page.keyboard.press('Escape'); } catch {} }
  await page.mouse.click(title.x - 22, title.y + title.h / 2);
  return (await read()) || { blurb: null, note: 'no-modal' };
}

// ---------- main loop ----------
let done = 0, okN = 0, failN = 0;
for (const v of Object.values(results)) { v.blurb != null ? okN++ : failN++; }
const startedAt = nowISO();
await launch();

for (let idx = 0; idx < todo.length; idx++) {
  const item = todo[idx];
  if (idx > 0 && idx % 60 === 0) { log('recycle browser'); await recycle(); }
  let rec = null;
  for (let attempt = 1; attempt <= 3 && !rec; attempt++) {
    try {
      const r = await scrapeOne(item);
      if (r.note?.startsWith('wrong-page')) { rec = r; break; }
      if (r.note === 'no-title' && attempt < 3) { await recycle(); continue; }
      if (r.note === 'no-modal' && attempt < 3 && item.kind !== 'spot') { await sleep(1500); continue; }
      rec = r;
    } catch (e) {
      log('ERR', item.coin, attempt, String(e.message).slice(0, 120));
      if (attempt < 3) { try { await recycle(); } catch {} }
      else rec = { blurb: null, note: 'error:' + String(e.message).slice(0, 80) };
    }
  }
  rec ||= { blurb: null, note: 'unknown' };

  const val = { kind: item.kind, dex: item.dex ?? null, vol: Math.round(item.vol * 100) / 100, blurb: rec.blurb ?? null, at: nowISO() };
  if (rec.note !== 'ok') val.note = rec.note;
  results[item.coin] = val;
  atomicWrite(STATE, JSON.stringify(results, null, 1));
  fs.appendFileSync(JSONL, JSON.stringify({ key: item.coin, val }) + '\n');

  done++;
  val.blurb != null ? okN++ : failN++;
  log(`${done}/${todo.length} ${item.coin} -> ${val.blurb ? 'OK ' + val.blurb.length + 'ch' : 'NULL ' + rec.note}`);
  if (done % 100 === 0) fs.appendFileSync(PROGRESS, `${nowISO()} done=${Object.keys(results).length}/${total} ok=${okN} fail=${failN}\n`);
  await sleep(1000 + Math.floor(Math.random() * 1000));
}

try { await browser?.close(); } catch {}
const all = Object.values(results);
const good = all.filter(v => v.blurb != null).length;
fs.writeFileSync(DONE, [
  'COMPLETE',
  `total: ${total}`, `records: ${all.length}`, `ok: ${good}`, `failed: ${all.length - good}`,
  `started: ${startedAt}`, `finished: ${nowISO()}`,
  'failed keys: ' + (Object.entries(results).filter(([, v]) => v.blurb == null).map(([k]) => k).join(', ') || '(none)'),
].join('\n') + '\n');
log('DONE');
