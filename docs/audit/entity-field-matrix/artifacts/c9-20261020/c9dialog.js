const http = require('http');
const PORT = process.env.CDP_PORT || '9240';
const sleep = ms => new Promise(r => setTimeout(r, ms));
const req = (m, p) => new Promise((res, rej) => {
  const r = http.request({ host: '127.0.0.1', port: PORT, path: p, method: m }, x => {
    let d = ''; x.on('data', c => d += c); x.on('end', () => { try { res(JSON.parse(d)) } catch (e) { res(d) } });
  }); r.on('error', rej); r.end();
});

(async () => {
  const list = await req('GET', '/json/list');
  const page = (list || []).filter(x => x.type === 'page')[0];
  console.log('PAGE_URL:', String(page.url || '').slice(0, 90));

  const ws = new WebSocket(page.webSocketDebuggerUrl);
  const pend = new Map(); let idv = 0;
  const events = [];
  const send = (m, p) => new Promise((rs, rj) => {
    const i = ++idv; pend.set(i, { rs, rj });
    ws.send(JSON.stringify({ id: i, method: m, params: p || {} }));
    setTimeout(() => { if (pend.has(i)) { pend.delete(i); rj(new Error('to:' + m)) } }, 12000);
  });
  ws.addEventListener('message', e => {
    const j = JSON.parse(e.data);
    if (j.id && pend.has(j.id)) { const { rs, rj } = pend.get(j.id); pend.delete(j.id); j.error ? rj(new Error('ERR')) : rs(j.result); return }
    if (j.method === 'Page.javascriptDialogOpening') { events.push({ t: 'dialog', msg: j.params.message, type: j.params.type, url: j.params.url }) }
    if (j.method === 'Inspector.targetCrashed') { events.push({ t: 'crash' }) }
    if (j.method === 'Page.frameNavigated' && j.params.frame.parentId === undefined) { events.push({ t: 'nav', url: String(j.params.frame.url).slice(0, 90) }) }
  });
  await new Promise((res, rej) => { ws.onopen = res; ws.onerror = () => rej(new Error('ws')) });
  await send('Page.enable'); await send('Runtime.enable'); await send('Inspector.enable').catch(() => {});

  // 直接尝试 eval（若 renderer 仍卡，会超时）
  const EV = async (x) => { try { const r = await send('Runtime.evaluate', { expression: x, returnByValue: true }); return (r && r.result) ? r.result.value : null } catch (e) { return '__FAIL__' } };
  console.log('EVAL_NOW:', JSON.stringify(await EV('1+1')));

  // 检查是否存在待处理 dialog
  for (let i = 0; i < 3; i++) {
    try { await send('Page.handleJavaScriptDialog', { accept: false }); console.log('DIALOG_DISMISSED@' + i) } catch (e) { console.log('NO_DIALOG@' + i); break }
    await sleep(800);
  }
  console.log('EVAL_AFTER_DISMISS:', JSON.stringify(await EV('1+1')));
  console.log('EVENTS:', JSON.stringify(events.slice(0, 8)));
  ws.close(); process.exit(0);
})().catch(e => { console.log('ERR', e.message); process.exit(1) });
