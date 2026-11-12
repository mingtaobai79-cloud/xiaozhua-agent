// 抽取 webpack chunk 里的权威表为 JSON。
// 用法: node extract_chunk_tables.mjs <unpacked-dir> <module-name|path...> [--json out.json]
// 例:  node extract_chunk_tables.mjs D:/.../udc-frontend/unpacked module-65420 module-31623 --json tables.json
// 说明: chunk 是 ESM，但内联 webpack `require(id)`；这里注入 require stub 后动态 import 求值。
import fs from 'fs';
import path from 'path';

const STUB = "const require = (id) => new Proxy({}, { get: () => (id) => new Proxy({}, { get: () => 'STUB' }) });\n";

const argv = process.argv.slice(2);
let outPath = null;
const oi = argv.indexOf('--json');
if (oi >= 0) { outPath = argv[oi + 1]; argv.splice(oi, 2); }
const dir = argv.shift();
const mods = argv;
if (!dir || !mods.length) {
  console.error('usage: node extract_chunk_tables.mjs <unpacked-dir> <module-name...> [--json out.json]');
  process.exit(2);
}

function resolveFile(dir, mod) {
  if (path.isAbsolute(mod) && fs.existsSync(mod)) return mod;
  let f = path.join(dir, mod.endsWith('.js') ? mod : mod + '.js');
  if (fs.existsSync(f)) return f;
  const target = path.basename(f);
  const stack = [dir];
  while (stack.length) {
    const d = stack.pop();
    for (const e of fs.readdirSync(d, { withFileTypes: true })) {
      const p = path.join(d, e.name);
      if (e.isDirectory()) stack.push(p);
      else if (e.name === target) return p;
    }
  }
  throw new Error('chunk not found: ' + mod);
}

const out = {};
for (const mod of mods) {
  const file = resolveFile(dir, mod);
  const src = fs.readFileSync(file, 'utf8');
  const names = [...src.matchAll(/export let ([A-Za-z_$0-9]+)/g)].map((m) => m[1]);
  const tmp = path.join(path.dirname(file), '.' + path.basename(file, '.js') + '.probe.mjs');
  fs.writeFileSync(tmp, STUB + src);
  let m;
  try {
    m = await import('file:///' + tmp.replace(/\\/g, '/') + '?t=' + Date.now());
  } finally {
    try { fs.unlinkSync(tmp); } catch (e) { /* ignore */ }
  }
  const rec = {};
  for (const n of names) rec[n] = (m[n] instanceof Map) ? Object.fromEntries(m[n]) : m[n];
  out[path.basename(file)] = rec;
  console.log('===', path.basename(file), ':', names.join(', '));
}

const json = JSON.stringify(out, null, 2);
if (outPath) { fs.writeFileSync(outPath, json); console.log('written', outPath); }
else console.log(json);
