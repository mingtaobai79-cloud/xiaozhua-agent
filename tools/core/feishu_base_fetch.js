// 在已登录页面上下文里直接 fetch 记录接口，拿全量记录 + 字段schema
const puppeteer = require('D:/software/hermes/node/node_modules/puppeteer');
const fs = require('fs');
const OUT = 'D:/work/chit/xiaozhua-agent/docs/audit/evidence/feishu-base';
const TOKEN = 'VJllbmPzqaApOQsAe5xctJc2nXe';
const TBL = 'tblqrIj6UB6kWpGF';
const VIEW = 'vewDbKLOB1';

(async () => {
  const browser = await puppeteer.connect({ browserURL: 'http://127.0.0.1:9222', defaultViewport: null });
  const pages = await browser.pages();
  const page = pages.find(p => p.url().includes(TOKEN));
  if (!page) { console.log('NO_PAGE'); process.exit(1); }

  const result = await page.evaluate(async (TOKEN, TBL, VIEW) => {
    const out = {};
    const urls = {
      records: `/space/api/v1/bitable/${TOKEN}/records?tableId=${TBL}&viewId=${VIEW}&offset=0&limit=3000&tableID=${TBL}&viewID=${VIEW}&removeFmlExtra=true&viewLazyLoad=true`,
      clientvars: `/space/api/v1/bitable/${TOKEN}/clientvars?tableID=${TBL}&viewID=${VIEW}&recordLimit=200&ondemandLimit=200&needBase=true&viewLazyLoad=true&ondemandVer=2&openType=0&noMissCS=true&optimizationFlag=1&removeFmlExtra=true`,
      fields: `/space/api/bitable/${TOKEN}/block_info?table=${TBL}`,
    };
    for (const [k, u] of Object.entries(urls)) {
      try {
        const r = await fetch(u, { credentials: 'include', headers: { 'accept': 'application/json' } });
        const t = await r.text();
        out[k] = { status: r.status, len: t.length, body: t.slice(0, 3000000) };
      } catch (e) { out[k] = { error: String(e) }; }
    }
    return out;
  }, TOKEN, TBL, VIEW);

  for (const [k, v] of Object.entries(result)) {
    console.log(k, '→', v.status || v.error, v.len || 0);
    if (v.body) fs.writeFileSync(`${OUT}/api_${k}.json`, v.body, 'utf8');
  }
  await browser.disconnect();
})();
