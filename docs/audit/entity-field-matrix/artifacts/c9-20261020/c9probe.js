const http = require('http');
const fs = require('fs');

const PORT = process.env.CDP_PORT || '9240';
const EID = '4796455827714164161';
const APPID = '8704025620829192834';

const sleep = ms => new Promise(r => setTimeout(r, ms));
const req = (m, p, port) => new Promise((res, rej) => {
  const r = http.request({ host: '127.0.0.1', port: port || PORT, path: p, method: m }, x => {
    let d = ''; x.on('data', c => d += c); x.on('end', () => { try { res(JSON.parse(d)) } catch (e) { res(d) } });
  }); r.on('error', rej); r.end();
});

(async () => {
  // 0. 端口存活
  const ver = await req('GET', '/json/version').catch(() => null);
  if (!ver || !ver.webSocketDebuggerUrl) { console.log('PROBE_PORT_DOWN'); process.exit(11) }
  console.log('PORT_UP:', PORT, '|', ver.Browser);

  const cred = JSON.parse(fs.readFileSync('D:/software/多agent协助/agent-collaboration/shared-credentials/test2-web-credential.json', 'utf8'));
  const pairs = (cred.cookie || '').split(';').map(s => s.trim()).filter(Boolean).map(s => {
    const i = s.indexOf('='); return i > 0 ? { name: s.slice(0, i).trim(), value: s.slice(i + 1).trim() } : null;
  }).filter(Boolean);
  console.log('COOKIE_PAIRS:', pairs.length);

  const list = await req('GET', '/json/list');
  const page = (list || []).filter(x => x.type === 'page')[0];
  if (!page) { console.log('NO_PAGE'); process.exit(12) }

  const ws = new WebSocket(page.webSocketDebuggerUrl);
  const pend = new Map(); let idv = 0;
  const send = (m, p) => new Promise((rs, rj) => {
    const i = ++idv; pend.set(i, { rs, rj });
    ws.send(JSON.stringify({ id: i, method: m, params: p || {} }));
    setTimeout(() => { if (pend.has(i)) { pend.delete(i); rj(new Error('to:' + m)) } }, 30000);
  });
  ws.addEventListener('message', e => {
    const j = JSON.parse(e.data);
    if (j.id && pend.has(j.id)) { const { rs, rj } = pend.get(j.id); pend.delete(j.id); j.error ? rj(new Error('cdp-err')) : rs(j.result) }
  });
  await new Promise((res, rej) => { ws.onopen = res; ws.onerror = () => rej(new Error('ws-fail')) });

  // 必须先 Runtime.enable 再 evaluate
  await send('Page.enable');
  await send('Network.enable');
  await send('Runtime.enable');
  console.log('DOMAINS: Page/Network/Runtime enabled');

  const EV = async (x, label) => {
    try {
      const r = await send('Runtime.evaluate', { expression: x, returnByValue: true });
      return (r && r.result) ? r.result.value : null;
    } catch (e) { console.log('EVAL_FAIL:', label, e.message); return '__EVAL_FAIL__' }
  };

  // 1. renderer 基础可求值（about:blank）
  const base = await EV('1+1', 'baseline');
  console.log('EVAL_BASELINE:', JSON.stringify(base));
  if (base !== 2) { console.log('PROBE_FAIL: renderer 不可求值'); ws.close(); process.exit(21) }

  // 2. 注入 cookie
  for (const p of pairs) {
    for (const dom of ['.changhongit.com', 'lowcode-test2.changhongit.com']) {
      try { await send('Network.setCookie', { name: p.name, value: p.value, domain: dom, path: '/', secure: true, sameSite: 'None' }) } catch (e) {}
    }
  }
  const ck = await send('Network.getCookies', { urls: ['https://lowcode-test2.changhongit.com/main/'] });
  console.log('COOKIES_SET:', (ck.cookies || []).length, (ck.cookies || []).map(c => c.name).join(','));

  // 3. 导航到设计器
  await send('Page.navigate', { url: 'https://lowcode-test2.changhongit.com/main/child-frame/udc/app-design/entity?appId=' + APPID });
  let tree = false, tries = 0;
  for (let i = 0; i < 16; i++) {
    await sleep(4500); tries++;
    const t = await EV('!!document.querySelector(".ant-tree")', 'tree@' + i);
    if (t === '__EVAL_FAIL__') { console.log('PROBE_RENDERER_DIED@' + i); break }
    if (t) { tree = true; console.log('TREE_READY@' + i); break }
  }
  console.log('PROBE_RESULT:', JSON.stringify({ tree, tries }));
  if (!tree) {
    const url = await EV('location.href', 'url');
    const len = await EV('(document.body.innerText||"").length', 'len');
    const txt = await EV('(document.body.innerText||"").replace(/\\s+/g," ").slice(0,140)', 'txt');
    console.log('FINAL_URL:', String(url).slice(0, 90));
    console.log('BODY_LEN:', len);
    console.log('BODY_TXT:', txt);
    console.log('PROBE_FAIL');
    ws.close(); process.exit(22)
  }
  console.log('PROBE_OK');
  ws.close(); process.exit(0);
})().catch(e => { console.log('ERR', e.message); process.exit(1) });
