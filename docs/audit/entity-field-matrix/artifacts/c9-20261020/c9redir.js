const http = require('http');
const sleep = ms => new Promise(r => setTimeout(r, ms));
const PORT = 9223;
const TARGET = 'https://lowcode-test2.changhongit.com/main/child-frame/udc/app-design/entity?appId=8704025620829192834';

const get = p => new Promise((res, rej) => {
  http.get({ host: '127.0.0.1', port: PORT, path: p }, r => {
    let d = ''; r.on('data', c => d += c); r.on('end', () => { try { res(JSON.parse(d)) } catch (e) { res(null) } });
  }).on('error', rej);
});

(async () => {
  const list = await get('/json/list');
  const page = (list || []).filter(x => x.type === 'page')[0];
  const ws = new WebSocket(page.webSocketDebuggerUrl);
  const pend = new Map(); let idv = 0;
  const navs = [], docs = [], dialogs = [];
  const send = (m, p) => new Promise((rs, rj) => {
    const i = ++idv; pend.set(i, { rs, rj });
    ws.send(JSON.stringify({ id: i, method: m, params: p || {} }));
    setTimeout(() => { if (pend.has(i)) { pend.delete(i); rj(new Error('to:' + m)) } }, 25000);
  });
  ws.addEventListener('message', e => {
    const j = JSON.parse(e.data);
    if (j.id && pend.has(j.id)) { const { rs, rj } = pend.get(j.id); pend.delete(j.id); j.error ? rj(new Error('cdp')) : rs(j.result); return }
    if (j.method === 'Page.frameNavigated' && !j.params.frame.parentId) navs.push(String(j.params.frame.url).slice(0, 120));
    if (j.method === 'Network.requestWillBeSent' && j.params.type === 'Document') docs.push({ u: String(j.params.request.url).slice(0, 110), redir: !!j.params.redirectResponse });
    if (j.method === 'Page.javascriptDialogOpening') dialogs.push({ msg: j.params.message, type: j.params.type });
  });
  await new Promise((res, rej) => { ws.onopen = res; ws.onerror = () => rej(new Error('ws')) });
  await send('Page.enable'); await send('Network.enable'); await send('Runtime.enable');
  const EV = async x => { try { const r = await send('Runtime.evaluate', { expression: x, returnByValue: true }); return (r && r.result) ? r.result.value : null } catch (e) { return '__DEAD__' } };

  console.log('BEFORE_URL:', String(await EV('location.href')).slice(0, 110));
  navs.length = 0; docs.length = 0;
  await send('Page.navigate', { url: TARGET }).then(r => console.log('NAV_RESULT:', JSON.stringify(r))).catch(e => console.log('NAV_ERR:', e.message));
  await sleep(22000);

  console.log('FINAL_URL:', String(await EV('location.href')).slice(0, 110));
  console.log('NAV_CHAIN:', JSON.stringify(navs));
  console.log('DOC_REQS:', JSON.stringify(docs.slice(0, 8)));
  console.log('DIALOGS:', JSON.stringify(dialogs));
  const st = await EV(`(function(){
    var t=(document.body.innerText||'');
    return JSON.stringify({
      loginPage: /账号密码|密码登录|短信登录|扫码登录|忘记密码/.test(t),
      hasNotesLogin: /notes/i.test(t),
      tree: !!document.querySelector('.ant-tree'),
      maxRows: (function(){var m=0;document.querySelectorAll('table').forEach(function(x){var n=x.querySelectorAll('tbody tr').length;if(n>m)m=n;});return m})(),
      len: t.length,
      hint: t.replace(/\\s+/g,' ').slice(0,120)
    });
  })()`);
  console.log('FINAL_STATE:', st);
  ws.close(); process.exit(0);
})().catch(e => { console.log('ERR', e.message); process.exit(1) });
