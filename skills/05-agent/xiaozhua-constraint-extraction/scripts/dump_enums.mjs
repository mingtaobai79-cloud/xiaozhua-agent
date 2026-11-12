/* dump 枚举值域（双模式正则，无参/带参枚举常量都抓）。
 * 用法: node dump_enums.mjs <反编译输出根目录> [--json out.json]
 * 例:  node dump_enums.mjs D:/.../serialnumber-java --json enums.json
 * 输出: { 枚举名: { constant: 构造参数(中文已解码) 或 null } }
 */
import fs from 'fs';
import path from 'path';

const argv = process.argv.slice(2);
let outPath = null;
const oi = argv.indexOf('--json');
if (oi >= 0) { outPath = argv[oi + 1]; argv.splice(oi, 2); }
const root = argv.shift();
if (!root) {
  console.error('usage: node dump_enums.mjs <反编译输出根目录> [--json out.json]');
  process.exit(2);
}

function walk(dir, acc = []) {
  for (const e of fs.readdirSync(dir, { withFileTypes: true })) {
    const p = path.join(dir, e.name);
    if (e.isDirectory()) walk(p, acc);
    else if (e.name.endsWith('Enum.java')) acc.push(p);
  }
  return acc;
}

const result = {};
for (const file of walk(root)) {
  const t = fs.readFileSync(file, 'utf8');
  const withArgs = new Map();
  for (const m of t.matchAll(/^\s+([A-Z][A-Z0-9_]*)\s*\((.*?)\),/gm)) {
    let args = m[2];
    try { args = Buffer.from(args, 'binary').toString('utf8'); } catch (e) { /* keep raw */ }
    withArgs.set(m[1], args);
  }
  const noArgs = new Set();
  for (const m of t.matchAll(/^\s+([A-Z][A-Z0-9_]*)\s*[,;]/gm)) {
    if (!withArgs.has(m[1])) noArgs.add(m[1]);
  }
  const entry = {};
  for (const [k, v] of withArgs) entry[k] = v;
  for (const k of noArgs) entry[k] = null;
  result[path.basename(file, '.java')] = entry;
}
const json = JSON.stringify(result, null, 1);
if (outPath) { fs.writeFileSync(outPath, json); console.log('written', outPath); }
else console.log(json);
