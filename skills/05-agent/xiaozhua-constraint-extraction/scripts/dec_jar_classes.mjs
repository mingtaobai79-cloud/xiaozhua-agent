/* 批量 CFR 反编译一个构件的全部 .class（递归子包）。
 * 用法: node dec_jar_classes.mjs <解压根目录> <输出目录> [--filter <子串>]
 * 例:  node dec_jar_classes.mjs D:/.../reference-src/boot-starter-serialnumber dec-out
 * 说明: 递归 os.walk 等价遍历，跳过 $ 内部类；每个 .class 配 --extraclasspath 解依赖。
 * 依赖: java + cfr.jar（路径见 SKILL.md 工具链）。
 */
import fs from 'fs';
import path from 'path';
import { execFileSync } from 'child_process';

const CFR = 'D:/software/hermes/skills/seeyon/03-v8-extension/seeyon-v8-spi/references/contract-index/tools/cfr.jar';
const argv = process.argv.slice(2);
let filter = null;
const fi = argv.indexOf('--filter');
if (fi >= 0) { filter = argv[fi + 1]; argv.splice(fi, 2); }
const [srcRoot, outRoot] = argv;
if (!srcRoot || !outRoot) {
  console.error('usage: node dec_jar_classes.mjs <解压根目录> <输出目录> [--filter 子串]');
  process.exit(2);
}

function walk(dir, acc = []) {
  for (const e of fs.readdirSync(dir, { withFileTypes: true })) {
    const p = path.join(dir, e.name);
    if (e.isDirectory()) walk(p, acc);
    else if (e.name.endsWith('.class') && !e.name.includes('$')) acc.push(p);
  }
  return acc;
}

const classes = walk(srcRoot).filter((f) => !filter || f.includes(filter));
let n = 0;
for (const full of classes) {
  const rel = path.relative(srcRoot, full).replace(/\.class$/, '.java');
  const out = path.join(outRoot, rel);
  if (fs.existsSync(out)) continue;
  fs.mkdirSync(path.dirname(out), { recursive: true });
  try {
    const stdout = execFileSync('java', ['-jar', CFR, full, '--extraclasspath', srcRoot],
      { maxBuffer: 64 * 1024 * 1024 });
    fs.writeFileSync(out, stdout);
    n++;
  } catch (e) {
    console.error('ERR', rel, String(e.message).slice(0, 120));
  }
}
console.log(`decompiled: ${n} of ${classes.length}`);
