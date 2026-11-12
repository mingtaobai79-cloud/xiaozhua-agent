// 记录页面所有 API 请求（方法/URL/postData），并滚动表格触发懒加载
const puppeteer = require('D:/software/hermes/node/node_modules/puppeteer');
const fs = require('fs');

const OUT = 'D:/work/chit/xiaozhua-agent/docs/audit/evidence/feishu-base';
(async () => {
  const browser = await puppeteer.connect({ browserURL: 'http://127.0.0.1:9222', defaultViewport: null });
  const pages = await browser.pages();
  const page = pages.find(p => p.url().includes('VJllbmPzqaApOQsAe5xctJc2nXe'));
  if (!page) { console.log('NO_PAGE'); process.exit(1); }

  const reqs = [];
  page.on('request', (r) => {
    const u = r.url();
    if (/feishu\.cn/.test(u) && !/feishucdn|static|\.js|\.css|\.png|\.svg|\.woff/.test(u)) {
      reqs.push({ m: r.method(), u, post: (r.postData() || '').slice(0, 800) });
    }
  });

  await page.reload({ waitUntil: 'networkidle2', timeout: 90000 }).catch(e => console.log('reload:', e.message));
  await new Promise(r => setTimeout(r, 12000));

  // 滚动/翻页触发记录加载
  await page.evaluate(() => {
    const sc = document.querySelectorAll('[class*=grid] [class*=scroll], [class*=virtual], [class*=table]');
    sc.forEach(e => { try { e.scrollTop = e.scrollHeight; } catch (x) {} });
    window.scrollTo(0, document.body.scrollHeight);
  }).catch(() => {});
  await new Promise(r => setTimeout(r, 4000));
  await page.keyboard.press('PageDown').catch(() => {});
  await new Promise(r => setTimeout(r, 4000));

  fs.writeFileSync(OUT + '/requests.jsonl', reqs.map(r => JSON.stringify(r)).join('\n'), 'utf8');
  console.log('API 请求数:', reqs.length);
  const seen = new Set();
  for (const r of reqs) {
    const key = r.u.split('?')[0];
    if (seen.has(key + r.m)) continue;
    seen.add(key + r.m);
    console.log(' ', r.m, r.u.slice(0, 165));
  }
  console.log('DOM chars:', (await page.evaluate(() => document.body.innerText)).length);
  await browser.disconnect();
})();
