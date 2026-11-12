// 通过 CDP(9222) 接管已登录的 Debug Edge，抓飞书多维表格：DOM 文本 + 内部 JSON 响应
const puppeteer = require('D:/software/hermes/node/node_modules/puppeteer');
const fs = require('fs');
const path = require('path');

const OUT = 'D:/work/chit/seeyon-agent/docs/audit/evidence/feishu-base';
const TARGET = 'https://changhongit.feishu.cn/base/VJllbmPzqaApOQsAe5xctJc2nXe?table=tblqrIj6UB6kWpGF&view=vewDbKLOB1';

(async () => {
  fs.mkdirSync(OUT, { recursive: true });
  const browser = await puppeteer.connect({ browserURL: 'http://127.0.0.1:9222', defaultViewport: null });
  const pages = await browser.pages();
  let page = pages.find(p => p.url().includes('VJllbmPzqaApOQsAe5xctJc2nXe'));
  if (!page) { page = pages.find(p => p.url().includes('feishu.cn')); }
  if (!page) { console.log('NO_PAGE'); process.exit(1); }
  console.log('PAGE:', page.url());

  const captured = [];
  page.on('response', async (res) => {
    try {
      const url = res.url();
      const ct = (res.headers()['content-type'] || '');
      if (!/json|javascript|text/.test(ct)) return;
      if (!/(bitable|base|record|table|sheet|space\/api)/i.test(url)) return;
      const txt = await res.text();
      if (txt && txt.length > 50) captured.push({ url, status: res.status(), body: txt });
    } catch (e) { /* ignore */ }
  });

  await page.reload({ waitUntil: 'networkidle2', timeout: 90000 }).catch(e => console.log('reload warn:', e.message));
  await new Promise(r => setTimeout(r, 8000));

  const dom = await page.evaluate(() => document.body.innerText);
  fs.writeFileSync(path.join(OUT, 'dom-innertext.txt'), dom, 'utf8');
  console.log('DOM chars:', dom.length);

  fs.writeFileSync(path.join(OUT, 'network.jsonl'),
    captured.map(c => JSON.stringify({ url: c.url, status: c.status, len: c.body.length, body: c.body.slice(0, 400000) })).join('\n'), 'utf8');
  console.log('captured responses:', captured.length);
  for (const c of captured.slice(0, 40)) console.log('  -', c.status, c.body.length, c.url.slice(0, 150));
  console.log('OUT_DIR:', OUT);
  await browser.disconnect();
})();
