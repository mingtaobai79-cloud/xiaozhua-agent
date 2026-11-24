const http = require('http');
const fs = require('fs');
const sleep = ms => new Promise(r => setTimeout(r, ms));
const req = (m, p) => new Promise((res, rej) => {
  const r = http.request({ host: '127.0.0.1', port: 9223, path: p, method: m }, x => {
    let d = ''; x.on('data', c => d += c); x.on('end', () => { try { res(JSON.parse(d)) } catch (e) { res(d) } });
  }); r.on('error', rej); r.end();
});
const EID = '4796455827714164161';
const FNAME = 'zzprobeDate01';

(async () => {
  const cred = JSON.parse(fs.readFileSync('D:/software/多agent协助/agent-collaboration/shared-credentials/test2-web-credential.json', 'utf8'));
  const pairs = (cred.cookie || '').split(';').map(s => s.trim()).filter(Boolean).map(s => {
    const i = s.indexOf('='); return i > 0 ? { name: s.slice(0, i).trim(), value: s.slice(i + 1).trim() } : null;
  }).filter(Boolean);
  console.log('COOKIE_PAIRS:', pairs.length);

  const all = await req('GET', '/json/list');
  const page = all.filter(x => x.type === 'page')[0];
  const ws = new WebSocket(page.webSocketDebuggerUrl);
  const pend = new Map(); let idv = 0;
  const send = (m, p) => new Promise((rs, rj) => {
    const i = ++idv; pend.set(i, { rs, rj });
    ws.send(JSON.stringify({ id: i, method: m, params: p || {} }));
    setTimeout(() => { if (pend.has(i)) { pend.delete(i); rj(new Error('to:' + m)) } }, 45000);
  });
  const hits = [];
  ws.addEventListener('message', e => {
    const j = JSON.parse(e.data);
    if (j.id && pend.has(j.id)) { const { rs, rj } = pend.get(j.id); pend.delete(j.id); j.error ? rj(new Error('e')) : rs(j.result); return }
    if (j.method === 'Network.requestWillBeSent' && j.params.request.url.indexOf('udc/graphql') >= 0) {
      hits.push({ op: ((j.params.request.postData || '').match(/(udc[A-Za-z]+)/) || [])[1] || '?', post: j.params.request.postData || '', rid: j.params.requestId });
    }
  });
  await new Promise((res, rej) => { ws.onopen = res; ws.onerror = () => rej(new Error('ws')) });
  await send('Page.enable'); await send('Network.enable'); await send('Runtime.enable');
  const EV = x => send('Runtime.evaluate', { expression: x, returnByValue: true }).then(r => (r && r.result) ? r.result.value : null).catch(() => null);
  const click = async (x, y, w) => {
    await send('Input.dispatchMouseEvent', { type: 'mouseMoved', x, y }); await sleep(200);
    await send('Input.dispatchMouseEvent', { type: 'mousePressed', x, y, button: 'left', clickCount: 1 }); await sleep(140);
    await send('Input.dispatchMouseEvent', { type: 'mouseReleased', x, y, button: 'left', clickCount: 1 }); await sleep(w || 1800);
  };
  const dclick = async (x, y) => {
    await send('Input.dispatchMouseEvent', { type: 'mouseMoved', x, y }); await sleep(160);
    await send('Input.dispatchMouseEvent', { type: 'mousePressed', x, y, button: 'left', clickCount: 1 }); await sleep(80);
    await send('Input.dispatchMouseEvent', { type: 'mouseReleased', x, y, button: 'left', clickCount: 1 }); await sleep(90);
    await send('Input.dispatchMouseEvent', { type: 'mousePressed', x, y, button: 'left', clickCount: 2 }); await sleep(70);
    await send('Input.dispatchMouseEvent', { type: 'mouseReleased', x, y, button: 'left', clickCount: 2 }); await sleep(1200);
  };
  const key = async (k, code, vk) => {
    await send('Input.dispatchKeyEvent', { type: 'keyDown', key: k, code, windowsVirtualKeyCode: vk, nativeVirtualKeyCode: vk });
    await send('Input.dispatchKeyEvent', { type: 'keyUp', key: k, code, windowsVirtualKeyCode: vk, nativeVirtualKeyCode: vk });
    await sleep(300);
  };
  const FIND = `(function(){
    var best=null,bn=-1;
    document.querySelectorAll('table').forEach(function(t){
      var n=t.querySelectorAll('tbody tr').length; if(n<5) return;
      var s=(t.innerText||''); if(s.indexOf('操作时间')>=0) return;
      if(s.indexOf('方案编码')<0 && s.indexOf('zzprobe')<0) return;
      if(n>bn){bn=n;best=t}
    });
    window.__FT=best; return best?String(best.querySelectorAll('tbody tr').length):'-1';
  })()`;

  // 只注入父域一次，避免同名 cookie 重复（上轮探测出现 6 条 = 3x2）
  await send('Network.clearBrowserCookies').catch(() => {});
  for (const p of pairs) {
    try { await send('Network.setCookie', { name: p.name, value: p.value, domain: '.changhongit.com', path: '/', secure: true, sameSite: 'None' }) } catch (e) {}
  }
  const ckChk = await send('Network.getCookies', { urls: ['https://lowcode-test2.changhongit.com/main/'] }).catch(() => null);
  const ckNames = ((ckChk && ckChk.cookies) || []).map(c => c.name);
  console.log('COOKIES_VERIFIED:', ckNames.length, ckNames.join(','));
  if (ckNames.length !== pairs.length) { console.log('ABORT_COOKIE_COUNT:', ckNames.length, '!=', pairs.length); ws.close(); process.exit(4) }
  await send('Page.navigate', { url: 'https://lowcode-test2.changhongit.com/main/child-frame/udc/app-design/entity?appId=8704025620829192834' });
  // 先确认 renderer 在导航后仍可求值（早期区分 renderer 挂死 vs 页面未就绪）
  let alive = false;
  for (let i = 0; i < 6; i++) {
    await sleep(3000);
    const probe = await EV('1+1');
    if (probe === '__EVAL_FAIL_NOW__' || probe === null) { console.log('RENDERER_DEAD@' + i); ws.close(); process.exit(31) }
    if (probe === 2) { alive = true; console.log('RENDERER_ALIVE@' + i); break }
  }
  if (!alive) { console.log('RENDERER_NO_EVAL'); ws.close(); process.exit(32) }
  let ok = false;
  for (let i = 0; i < 12; i++) { await sleep(4000); if (await EV('!!document.querySelector(".ant-tree")')) { ok = true; console.log('LOAD@' + i); break } }
  if (!ok) { console.log('NO_TREE'); ws.close(); process.exit(3) }

  console.log('SEL:', await EV(`(function(){
    var t=document.querySelector('.ant-tree'); if(!t) return 'NOTREE';
    var ks=Object.keys(t).filter(function(k){return k.indexOf('__reactFiber')>=0});
    var f=t[ks[0]], p=null;
    for(var i=0;i<16&&f;i++,f=f.return){ var mp=f.memoizedProps||{}; if(mp.treeData&&mp.treeData.length){p=mp;break} }
    if(!p) return 'NOPROPS';
    var node=null,par=null;
    (function w(a){ (a||[]).forEach(function(x){ if(String(x.key)==='${EID}') node=x; if((x.children||[]).some(function(c){return String(c.key)==='${EID}'})) par=x; if(x.children) w(x.children) }) })(p.treeData);
    if(!node) return 'NONODE';
    if(par){ try{ p.onExpand([String(par.key)],{expanded:true,node:par,nativeEvent:{}}) }catch(e){} }
    try{ p.onSelect(['${EID}'],{selected:true,node:node,selectedNodes:[node],nativeEvent:{},target:t}); return 'OK' }catch(e){ return 'THROW' }
  })()`));
  await sleep(11000);
  console.log('N0:', await EV(FIND));

  // 添加
  const ap = JSON.parse(await EV(`(function(){
    var bs=[...document.querySelectorAll('button')].filter(function(b){return (b.innerText||'').trim()==='添加'});
    var r=bs.map(function(b){var q=b.getBoundingClientRect();return {x:Math.round(q.x+q.width/2),y:Math.round(q.y+q.height/2),yt:Math.round(q.y)}}).filter(function(e){return e.yt>400});
    return r.length?JSON.stringify(r[r.length-1]):'{"e":1}';
  })()`));
  if (!ap.x) { console.log('NO_ADD_BTN'); ws.close(); process.exit(5) }
  await click(ap.x, ap.y, 2600);
  console.log('N1:', await EV(FIND));

  // 名称：双击 → Ctrl+A → Backspace 清空 → 输入
  const np = JSON.parse(await EV(`(function(){
    var t=window.__FT; var trs=[...t.querySelectorAll('tbody tr')];
    var r0=trs[trs.length-1]; r0.scrollIntoView({block:'center'});
    var tds=[...r0.querySelectorAll('td')]; var r=tds[1].getBoundingClientRect();
    return JSON.stringify({x:Math.round(r.x+30),y:Math.round(r.y+r.height/2)});
  })()`));
  await dclick(np.x, np.y);

  // 真实 Ctrl+A：必须带 modifiers=2 (Ctrl)
  const ctrlA = async () => {
    await send('Input.dispatchKeyEvent', { type: 'keyDown', key: 'Control', code: 'ControlLeft', windowsVirtualKeyCode: 17, nativeVirtualKeyCode: 17, modifiers: 2 });
    await sleep(80);
    await send('Input.dispatchKeyEvent', { type: 'keyDown', key: 'a', code: 'KeyA', windowsVirtualKeyCode: 65, nativeVirtualKeyCode: 65, modifiers: 2 });
    await sleep(80);
    await send('Input.dispatchKeyEvent', { type: 'keyUp', key: 'a', code: 'KeyA', windowsVirtualKeyCode: 65, nativeVirtualKeyCode: 65, modifiers: 2 });
    await sleep(80);
    await send('Input.dispatchKeyEvent', { type: 'keyUp', key: 'Control', code: 'ControlLeft', windowsVirtualKeyCode: 17, nativeVirtualKeyCode: 17, modifiers: 0 });
    await sleep(300);
  };
  await ctrlA();
  console.log('SEL_RANGE:', await EV(`(function(){
    var el=document.activeElement; if(!el) return 'NOFOCUS';
    return JSON.stringify({selStart:el.selectionStart, selEnd:el.selectionEnd, val:el.value});
  })()`));
  await key('Backspace', 'Backspace', 8);
  await sleep(400);

  // 兜底：仍非空则连发 Backspace 清空
  let cur1 = await EV(`(document.activeElement&&document.activeElement.value)||''`);
  let guard = 0;
  while (cur1 && cur1.length > 0 && guard < 40) {
    await send('Input.dispatchKeyEvent', { type: 'keyDown', key: 'Backspace', code: 'Backspace', windowsVirtualKeyCode: 8, nativeVirtualKeyCode: 8 });
    await send('Input.dispatchKeyEvent', { type: 'keyUp', key: 'Backspace', code: 'Backspace', windowsVirtualKeyCode: 8, nativeVirtualKeyCode: 8 });
    await sleep(120);
    cur1 = await EV(`(document.activeElement&&document.activeElement.value)||''`);
    guard++;
  }
  console.log('AFTER_CLEAR:', await EV(`(function(){
    var el=document.activeElement; return el? JSON.stringify({tag:el.tagName,val:el.value,cleared:(el.value==='')}):'NOFOCUS';
  })()`), 'guard=', guard);
  if (cur1 !== '') { console.log('ABORT_CLEAR_FAILED:', cur1); ws.close(); process.exit(8) }
  for (const ch of FNAME) { await send('Input.dispatchKeyEvent', { type: 'char', text: ch, unmodifiedText: ch }); await sleep(90) }
  await sleep(500);
  console.log('AFTER_TYPE:', await EV(`(function(){
    var el=document.activeElement; var v=el?el.value:null;
    return JSON.stringify({val:v, exact:(v==='${FNAME}'), len:(v||'').length});
  })()`));
  await key('Tab', 'Tab', 9);
  await sleep(1400);

  // 类型 → 日期（键盘过滤）
  const tp = JSON.parse(await EV(`(function(){
    var t=window.__FT; var trs=[...t.querySelectorAll('tbody tr')];
    var r0=trs[trs.length-1]; r0.scrollIntoView({block:'center'});
    var tds=[...r0.querySelectorAll('td')]; var c=tds[3].firstElementChild||tds[3];
    var r=c.getBoundingClientRect();
    return JSON.stringify({x:Math.round(r.x+30),y:Math.round(r.y+r.height/2)});
  })()`));
  await dclick(tp.x, tp.y);
  await sleep(1000);
  const sp = JSON.parse(await EV(`(function(){
    var sels=[...document.querySelectorAll('.ant-select')].filter(function(s){var r=s.getBoundingClientRect();return r.width>50&&r.height>10});
    var s=sels[sels.length-1]; if(!s) return '{"e":1}';
    var sel=s.querySelector('.ant-select-selector')||s; var r=sel.getBoundingClientRect();
    return JSON.stringify({x:Math.round(r.x+r.width/2),y:Math.round(r.y+r.height/2)});
  })()`));
  if (!sp.x) { console.log('NO_SELECT'); ws.close(); process.exit(6) }
  await click(sp.x, sp.y, 1800);
  await send('Input.insertText', { text: '日期' });
  await sleep(1600);
  console.log('FILTER:', await EV(`JSON.stringify([...document.querySelectorAll('.ant-select-item-option')].map(function(o){return (o.innerText||'').trim()}))`));
  await key('Enter', 'Enter', 13);
  await sleep(2000);

  const ROW = `(function(){
    var t=window.__FT; if(!t) return '-';
    var trs=[...t.querySelectorAll('tbody tr')];
    var tds=[...trs[trs.length-1].querySelectorAll('td')];
    return JSON.stringify({n:trs.length, c1:(tds[1].innerText||'').trim(), c3:(tds[3].innerText||'').trim().slice(0,50), open:document.querySelectorAll('.ant-select-open').length});
  })()`;
  console.log('ROW:', await EV(ROW));

  for (let k = 0; k < 3; k++) { if (!(await EV(`document.querySelectorAll('.ant-select-open').length`))) break; await key('Escape', 'Escape', 27) }
  await EV(`document.activeElement&&document.activeElement.blur&&document.activeElement.blur()`);
  await EV(`document.body.click()`);
  await sleep(1400);

  // 保存前双重核对：DOM 单元格文本 + 无警告
  console.log('PRE_SAVE:', await EV(`(function(){
    var t=window.__FT; var trs=[...t.querySelectorAll('tbody tr')];
    var tds=[...trs[trs.length-1].querySelectorAll('td')];
    var nm=(tds[1].innerText||'').trim();
    var b=[...document.querySelectorAll('button')].find(function(x){return (x.innerText||'').trim()==='保存'});
    var body=document.body.innerText||'';
    return JSON.stringify({cell_name:nm, exact:(nm==='${FNAME}'),
      dis:b?b.disabled:'NOBTN', open:document.querySelectorAll('.ant-select-open').length,
      warn:(body.indexOf('重建')>=0||body.indexOf('数据丢失')>=0||body.indexOf('数据损失')>=0)});
  })()`));

  const pre = JSON.parse(await EV(`(function(){
    var t=window.__FT; var trs=[...t.querySelectorAll('tbody tr')];
    var tds=[...trs[trs.length-1].querySelectorAll('td')];
    return JSON.stringify({nm:(tds[1].innerText||'').trim()});
  })()`));
  if (pre.nm !== FNAME) { console.log('ABORT_NAME_MISMATCH:', pre.nm); ws.close(); process.exit(7) }

  // 二次核对：重进名称单元格读 input.value 是否精确
  const np2 = JSON.parse(await EV(`(function(){
    var t=window.__FT; var trs=[...t.querySelectorAll('tbody tr')];
    var r0=trs[trs.length-1]; r0.scrollIntoView({block:'center'});
    var tds=[...r0.querySelectorAll('td')]; var r=tds[1].getBoundingClientRect();
    return JSON.stringify({x:Math.round(r.x+30),y:Math.round(r.y+r.height/2)});
  })()`));
  await dclick(np2.x, np2.y);
  const liveVal = await EV(`(document.activeElement&&document.activeElement.value)`);
  console.log('SAVE_PRE_INPUT:', JSON.stringify({val: liveVal, exact: liveVal === FNAME}));
  await key('Tab', 'Tab', 9);
  await sleep(900);
  if (liveVal !== FNAME) { console.log('ABORT_INPUT_MISMATCH:', liveVal); ws.close(); process.exit(9) }

  hits.length = 0;
  console.log('SAVE:', await EV(`(function(){
    var b=[...document.querySelectorAll('button')].find(function(x){return (x.innerText||'').trim()==='保存'});
    if(!b) return 'NO_BTN'; if(b.disabled) return 'DISABLED';
    var ks=Object.keys(b).filter(function(k){return k.indexOf('__reactProps')>=0});
    var p=ks.length?b[ks[0]]:{};
    if(typeof p.onClick!=='function') return 'NO_FN';
    try{ p.onClick({preventDefault:function(){},stopPropagation:function(){},currentTarget:b,target:b,nativeEvent:{}}); return 'CLICKED' }catch(e){ return 'THROW' }
  })()`));
  await sleep(15000);
  console.log('MSG:', await EV(`JSON.stringify([...document.querySelectorAll('.ant-message-notice-content')].map(function(e){return (e.innerText||'').trim()}))`));

  const out = [];
  for (const h of hits) {
    let rb = null;
    try { const r = await send('Network.getResponseBody', { requestId: h.rid }); rb = r.body } catch (e) {}
    out.push({ op: h.op, pl: (h.post || '').length, post: h.post, bl: rb ? rb.length : -1, body: rb });
  }
  fs.writeFileSync('C:/Users/白明涛/AppData/Local/Temp/c9save.json', JSON.stringify(out, null, 1), 'utf8');
  console.log('HITS:', JSON.stringify(out.map(x => ({ op: x.op, pl: x.pl, bl: x.bl }))));

  ws.close(); process.exit(0);
})().catch(e => { console.log('ERR', e.message); process.exit(1) });
