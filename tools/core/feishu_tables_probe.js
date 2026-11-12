// 查 base 内其他 table 的名字（block_info / ssr_cache_info / table meta）
const puppeteer = require('D:/software/hermes/node/node_modules/puppeteer');
const OUT = 'D:/work/chit/xiaozhua-agent/docs/audit/evidence/feishu-base';
const fs = require('fs');
const TOKEN = 'VJllbmPzqaApOQsAe5xctJc2nXe';
const TABLES = ['tblqrIj6UB6kWpGF', 'tblm5rHNgXNkbYCT', 'tblh2Mjfuz5K2VJo', 'tblB3NT2F9gRSJBt'];

(async () => {
  const browser = await puppeteer.connect({ browserURL: 'http://127.0.0.1:9222', defaultViewport: null });
  const pages = await browser.pages();
  const page = pages.find(p => p.url().includes(TOKEN));
  const res = await page.evaluate(async (TOKEN, TABLES) => {
    const out = {};
    for (const t of TABLES) {
      out[t] = {};
      const urls = {
        block_info: `/space/api/bitable/${TOKEN}/block_info?table=${t}`,
        cache: `/space/api/bitable/${TOKEN}/ssr_cache_info?table=${t}`,
        view_type: `/space/api/bitable/${TOKEN}/view_type?table=${t}`,
      };
      for (const [k, u] of Object.entries(urls)) {
        try {
          const r = await fetch(u, { credentials: 'include' });
          out[t][k] = { s: r.status, b: (await r.text()).slice(0, 3000) };
        } catch (e) { out[t][k] = { s: 0, b: String(e) }; }
      }
    }
    return out;
  }, TOKEN, TABLES);
  fs.writeFileSync(`${OUT}/other_tables.json`, JSON.stringify(res, null, 1), 'utf8');
  for (const t of TABLES) console.log(t, JSON.stringify(res[t]).slice(0, 700));
  await browser.disconnect();
})();
