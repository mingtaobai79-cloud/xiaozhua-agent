const http = require('http');
const sleep = ms => new Promise(r => setTimeout(r, ms));
const PORT = 9223;
const APPID = '8704025620829192834';
const TARGET = 'https://lowcode-test2.changhongit.com/main/child-frame/udc/app-design/entity?appId=' + APPID;

const get = p => new Promise((res, rej) => {
  http.get({ host: '127.0.0.1', port: PORT, path: p }, r => {
    let d = ''; r.on('data', c => d += c); r.on('end', () => { try { res(JSON.parse(d)) } catch (e) { res(null) } });
  }).on('error', rej);
});

(async () => {
  const list = await get('/json/list');
  const pages = (list || []).filter(x => x.type === 'page');
  console.log('PAGES:', pages.length);
  pages.forEach(p => console.log('  start:', String(p.url).slice(0, 90)));
  const page = pages[0];
  if (!page) { console.log('NO_PAGE'); process.exit(12) }

  const ws = new WebSocket(page.webSocketDebuggerUrl);
  const pend = new Map(); let idv = 0;
  const send = (m, p) => new Promise((rs, rj) => {
    const i = ++idv; pend.set(i, { rs, rj });
    ws.send(JSON.stringify({ id: i, method: m, params: p || {} }));
    setTimeout(() => { if (pend.has(i)) { pend.delete(i); rj(new Error('to:' + m)) } }, 25000);
  });
  ws.addEventListener('message', e => {
    const j = JSON.parse(e.data);
    if (j.id && pend.has(j.id)) { const { rs, rj } = pend.get(j.id); pend.delete(j.id); j.error ? rj(new Error('cdp')) : rs(j.result) }
  });
  await new Promise((res, rej) => { ws.onopen = res; ws.onerror = () => rej(new Error('ws')) });
  await send('Page.enable'); await send('Network.enable'); await send('Runtime.enable');

  const EV = async (x, tag) => {
    try { const r = await send('Runtime.evaluate', { expression: x, returnByValue: true }); return (r && r.result) ? r.result.value : null }
    catch (e) { console.log('EVAL_TIMEOUT@' + tag); return '__DEAD__' }
  };

  // 当前页基线
  const b0 = await EV('1+1', 'pre');
  console.log('PRE_BASELINE:', JSON.stringify(b0));
  console.log('PRE_URL:', String(await EV('location.href', 'pre-url')).slice(0, 90));

  // 只读导航（不注入 cookie）
  await send('Page.navigate', { url: TARGET });
  console.log('NAVIGATED');

  // G2: renderer 死 vs 未就绪
  let alive = false;
  for (let i = 0; i < 8; i++) {
    await sleep(3000);
    const v = await EV('1+1', 'g2-' + i);
    if (v === '__DEAD__') { console.log('RENDERER_DEAD@' + i); break }
    if (v === 2) { alive = true; console.log('RENDERER_ALIVE@' + i); break }
  }
  if (!alive) { console.log('VERDICT: BLOCKED-ENV (renderer dead)'); ws.close(); process.exit(31) }

  // 实质渲染判据
  let verdict = null;
  for (let i = 0; i < 15; i++) {
    await sleep(4000);
    const st = await EV(`(function(){
      var tree = document.querySelector('.ant-tree');
      var tables = document.querySelectorAll('table').length;
      var rows = 0;
      document.querySelectorAll('table').forEach(function(t){
        var n=t.querySelectorAll('tbody tr').length; if(n>rows) rows=n;
      });
      var txt=(document.body.innerText||'');
      return JSON.stringify({
        url: location.href.slice(0,90),
        tree: !!tree,
        tables: tables,
        maxRows: rows,
        len: txt.length,
        login: /账号密码|密码登录|短信登录|扫码登录|忘记密码/.test(txt),
        forbid: /403|无权限|Forbidden|访问被拒绝/.test(txt),
        bodyHint: txt.replace(/\\s+/g,' ').slice(0,110)
      });
    })()`, 'state-' + i);
    if (st === '__DEAD__') { console.log('DIED_DURING_RENDER@' + i); verdict = 'DEAD'; break }
    const s = JSON.parse(st);
    const live = s.tree && s.maxRows >= 5 && !s.login && !s.forbid;
    console.log('STATE@' + i + ':', st);
    if (live) { verdict = 'LIVE'; break }
    if (s.login || s.forbid) { verdict = s.login ? 'LOGIN' : 'FORBID'; break }
  }
  console.log('STEP1_VERDICT:', verdict);
  ws.close(); process.exit(verdict === 'LIVE' ? 0 : 33);
})().catch(e => { console.log('ERR', e.message); process.exit(1) });
