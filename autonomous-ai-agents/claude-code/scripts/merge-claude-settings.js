#!/usr/bin/env node
/**
 * 就地合并 Claude Code settings.json，不重写未触碰的字段。
 * 存在的理由：read_file 会把 token 掩码，任何「读出后整文件写回」都会把密钥写成占位符。
 *
 * 用法：
 *   node merge-claude-settings.js <settings.json> <patch.json> [--dry-run]
 *
 * patch.json 形如：
 * {
 *   "set":        { "permissions.defaultMode": "acceptEdits" },
 *   "addToArray": { "permissions.allow": ["Bash(python *)"],
 *                   "permissions.deny":  ["Bash(rm -rf *)"] }
 * }
 * set：点分路径赋值，缺的中间层自动建。addToArray：数组并集追加（已存在的跳过）。
 * 不做删除：本脚本只增改，删条目请手改。
 */
const fs = require('fs');
const path = require('path');

const [target, patchPath, ...flags] = process.argv.slice(2);
if (!target || !patchPath) {
  console.error('usage: node merge-claude-settings.js <settings.json> <patch.json> [--dry-run]');
  process.exit(2);
}
const dryRun = flags.includes('--dry-run');
const stripBOM = (s) => s.replace(/^\uFEFF/, '');
const getPath = (obj, dotted) => dotted.split('.').reduce((o, k) => (o == null ? o : o[k]), obj);
const setPath = (obj, dotted, val) => {
  const keys = dotted.split('.');
  let cur = obj;
  for (const k of keys.slice(0, -1)) {
    if (typeof cur[k] !== 'object' || cur[k] === null) cur[k] = {};
    cur = cur[k];
  }
  cur[keys.at(-1)] = val;
};

const raw = fs.readFileSync(target, 'utf8');
const cfg = JSON.parse(stripBOM(raw));
const patch = JSON.parse(fs.readFileSync(patchPath, 'utf8'));

const before = {
  env: JSON.stringify(cfg.env),
  token: cfg.env && cfg.env.ANTHROPIC_AUTH_TOKEN,
  topKeys: Object.keys(cfg),
  rawEnv: (cfg.env || {}).ANTHROPIC_BASE_URL,
};

const report = { changed: [], skipped: [], createdArrays: [] };

for (const [dotted, val] of Object.entries(patch.set || {})) {
  const old = getPath(cfg, dotted);
  if (JSON.stringify(old) === JSON.stringify(val)) { report.skipped.push(`${dotted} (already ${JSON.stringify(val)})`); continue; }
  setPath(cfg, dotted, val);
  report.changed.push(`${dotted}: ${JSON.stringify(old)} -> ${JSON.stringify(val)}`);
}

for (const [dotted, items] of Object.entries(patch.addToArray || {})) {
  let arr = getPath(cfg, dotted);
  if (!Array.isArray(arr)) {
    report.createdArrays.push(dotted);
    setPath(cfg, dotted, []);
    arr = getPath(cfg, dotted);
  }
  for (const it of items) {
    if (arr.includes(it)) { report.skipped.push(it); continue; }
    arr.push(it);
    report.changed.push(`+ ${dotted}[] ${it}`);
  }
}

const out = JSON.stringify(cfg, null, 2) + '\n';
if (!dryRun) {
  const stamp = new Date().toISOString().slice(0, 10);
  const bak = `${target}.bak-${stamp}`;
  if (!fs.existsSync(bak)) fs.copyFileSync(target, bak);
  report.backup = bak;
  fs.writeFileSync(target, Buffer.from(out, 'utf8')); // 无 BOM
} else {
  report.dryRun = out;
}

// ---- 写后自检：密钥/编码/结构一样都不能变 ----
if (!dryRun) {
  const buf = fs.readFileSync(target);
  const after = JSON.parse(stripBOM(buf.toString('utf8')));
  report.verify = {
    envUnchanged: JSON.stringify(after.env) === before.env,
    tokenUnchanged: ((after.env || {}).ANTHROPIC_AUTH_TOKEN) === before.token,
    tokenLen: before.token ? before.token.length : null,
    baseUrlUnchanged: (after.env || {}).ANTHROPIC_BASE_URL === before.rawEnv,
    topKeysSameOrder: JSON.stringify(Object.keys(after)) === JSON.stringify(before.topKeys),
    hasBOM: buf[0] === 0xEF && buf[1] === 0xBB && buf[2] === 0xBF,
    bytes: buf.length,
  };
  const bad = Object.entries(report.verify).filter(([k, v]) => v === false && k !== 'hasBOM');
  if (bad.length) { console.error('VERIFY FAILED', JSON.stringify(bad)); process.exit(1); }
}

console.log(JSON.stringify(report, null, 2));
