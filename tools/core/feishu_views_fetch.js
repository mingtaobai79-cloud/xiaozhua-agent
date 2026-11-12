// 拉取 待修改-汇总 / 汇总 / 挂起 视图的 clientvars，看分组(by)与顺序
const puppeteer = require('D:/software/hermes/node/node_modules/puppeteer');
const fs = require('fs');
const OUT = 'D:/work/chit/xiaozhua-agent/docs/audit/evidence/feishu-base';
const TOKEN = 'VJllbmPzqaApOQsAe5xctJc2nXe';
const TBL = 'tblqrIj6UB6kWpGF';
const VIEWS = { vew2YbbsTY: '待修改-汇总', vewUHHFITx: '汇总', vewQaFD315: '挂起' };

(async () => {
  const browser = await puppeteer.connect({ browserURL: 'http://127.0.0.1:9222', defaultViewport: null });
  const pages = await browser.pages();
  const page = pages.find(p => p.url().includes(TOKEN));
  const res = await page.evaluate(async (TOKEN, TBL, views) => {
    const out = {};
    for (const [vid, name] of Object.entries(views)) {
      const u = `/space/api/v1/bitable/${TOKEN}/clientvars?tableID=${TBL}&viewID=${vid}&recordLimit=200&ondemandLimit=200&needBase=true&viewLazyLoad=true&ondemandVer=2&openType=0&noMissCS=true&optimizationFlag=1&removeFmlExtra=true`;
      const r = await fetch(u, { credentials: 'include' });
      const t = await r.text();
      out[name] = { status: r.status, len: t.length, body: t.slice(0, 400000) };
    }
    return out;
  }, TOKEN, TBL, VIEWS);
  for (const [name, v] of Object.entries(res)) {
    console.log(name, '→', v.status, v.len);
    fs.writeFileSync(`${OUT}/view_${name}.json`, v.body, 'utf8');
  }
  await browser.disconnect();
})();
