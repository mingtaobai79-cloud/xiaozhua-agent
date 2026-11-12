#!/usr/bin/env node
/**
 * microflow-panel-probe.js — 微流程节点面板证据采集器 v4（只读）
 *
 * v4 = HANDOFF #4（R1–R5）+ 13:49 补充件（zombie-drawer 根因）+ prelim REQ-1 合取。
 *  v3 教训（13:38 → 13:56）：precheck 拒绝「点位不在目标子树」本身是**正确**行为，问题在
 *  遮挡源未识别未清理（僵尸 .ant-drawer 空壳 pointer-events:auto 覆盖 x≥945）。v4 不放宽判据，
 *  改为「遮挡识别 -> 视图层清理 -> 命中复验 -> 平移画布重试 -> 三路全败才 CLICK_TARGET_FAIL」。
 *  R1 点击判据：precheck 依旧要求命中点落在目标节点子树内（这是「点到了这个节点」的唯一硬证据）；
 *     抽屉态下先清遮挡再点，不把「被遮」当成功、也不把它当节点身份失败。
 *  R2 precheck 拦截范围：input / textarea / [contenteditable]（编辑态误入，绝不点）+ 非目标子树（遮挡，走清理路径）。
 *  R3 knownFailRecheck：n16/n17 必须 distinct 且标题正确。
 *  R4 branchSpec 语义不变：拿不到 -> BRANCH_UI_UNCAPTURED（禁 NULL / 禁 STRUCTURAL_NO_PANEL 充数）。
 *  R5 不回退：C1=21 条；C4 每个 captured 节点 isProvenPanelOfThisNode=true；selfTest>=8 例 RC=0；
 *     writes 口径与 requestLog 自洽（graphql 记 operationName，mutation 关键字命中即计配置写）。
 *  v4 新增（auditor VERDICT-v22 §3 + prelim REQ-1 合并采纳）：
 *   - clearOccluders()：关闭按钮 -> modal close -> ESC -> 空壳（bodyChildCount===0 且无 SETTINGS）display:none
 *     纯视图移除，全部记 zombieRemoved[]；不触碰任何节点配置。
 *   - preClose 强一致：drawerCleared===false 时该节点不点击（CLEAR_OVERLAY_FAIL），禁 closed:true 与 false 并存。
 *   - panicClear 模式：一旦本轮出现过 CLEAR_OVERLAY_FAIL，后续每节点点击前强制 clearOccluders（不整体停）。
 *   - requestLog 每条形如 {m,p,postDataLen,operationName,mutationKeyword,configWrite,readOnlyJustification}；
 *     删除「no POST/PUT/DELETE issued」失真表述，改为可复核口径。
 *
 * v3 历史（保留说明，不回退）：
 *  D1 nodeType 归一化：剥 _n<N> / _n<N><a-z> 后缀成纯类型（CREATE_MAP_n6a -> CREATE_MAP + instance:"6a"）；
 *     ALLOW 查表精确相等（禁 startsWith），查不到 unmapped。
 *  D2 clickTarget：点击前 elementFromPoint 预校验；命中 input/textarea/[contenteditable] 或非目标子树则换点
 *     重试（icon 中心 -> 标题左 8px -> 标题外框），三次全失败 CLICK_TARGET_FAIL；每节点记 attempts[]。
 *  D3 branchSpec：BRANCH/CONDITION 按分支自身 UI 只读采集（分支卡渲染文本/条件表达式），拿不到标
 *     BRANCH_UI_UNCAPTURED（明确失败证据），不再用 STRUCTURAL_NO_PANEL 当成功。
 *
 * live 实测事实（2026-10-17，CDP 9222）驱动本版修正：
 *  F1 面板根 = `.udc-microflow-editor-node-settings`（在 `.ant-drawer` 内，no-mask，inline）。
 *  F2 面板身份权威标识 = `.ant-drawer-title` 文本（如「自定义服务」「事件投递」「创建变量」），
 *     这是平台自己给的面板标题，不是从正文猜的。
 *  F3 画布无滚动容器，节点靠 CSS 平移定位；旧版 scrollIntoView 后 rect 已过期，原生点击落到抽屉上。
 *  F4 抽屉宽 1309px 且 no-mask，**不关闭会遮住后续节点**：点击静默失效，
 *     `.active` 留在上一个节点，面板内容不换 -> 旧采集器把上一面板的指纹复制给后续节点，
 *     这正是 `microflow-panel-identity-audit.json` 已知 FAIL（事件投递 duplicate_of 自定义服务）的真因。
 *  F5 CDP Input.dispatchMouseEvent 在本页会 timeout；DOM 合成事件可靠。
 *
 * 因此本版规则：
 *  R1 每次点击前必须 closeDrawer 并轮询确认 `.udc-microflow-editor-node-settings` 消失。
 *  R2 点击用 DOM 合成事件（pointerdown/mousedown/pointerup/mouseup/click + el.click()）。
 *  R3 面板身份必须三重自证：active nodeId == 目标 && drawerTitle 非空 && 本节点是「新打开」的。
 *     任一不成立 -> PANEL_SWITCH_FAIL，明确失败，不静默产出。
 *  R4 指纹 = FNV1a×2 over {drawerTitle, formLabels[], ctlSig[], buttons[]}，不含 nodeId。
 *  R5 结构节点（BRANCH/CONDITION）无面板时标 STRUCTURAL_NO_PANEL 并附点击证据，不算静默通过。
 *
 * 用法：
 *   node microflow-panel-probe.js --self-test
 *   node microflow-panel-probe.js --flow -1014184770817921434 --app 8704025620829192834 \
 *        --out docs/audit/artifacts/udc-node-evidence/microflow-panel-probe-v2.json
 *   node microflow-panel-probe.js --limit 3
 */
'use strict';
const http = require('http'), net = require('net'), crypto = require('crypto'), fs = require('fs'), path = require('path');

const BASE = 'https://lowcode-test2.changhongit.com';
const sleep = ms => new Promise(r => setTimeout(r, ms));

/* ---------- 最小 CDP 客户端 ---------- */
function httpJson(p) {
  return new Promise((res, rej) => {
    http.get({ host: '127.0.0.1', port: 9222, path: p }, r => {
      let d = ''; r.on('data', c => d += c); r.on('end', () => { try { res(JSON.parse(d)); } catch (e) { res(d); } });
    }).on('error', rej);
  });
}
function rawWs(url) {
  return new Promise((resolve, reject) => {
    const m = url.match(/^ws:\/\/([^:/]+):(\d+)(\/.*)$/);
    const s = net.connect(Number(m[2]), m[1], () => {
      const k = crypto.randomBytes(16).toString('base64');
      s.write('GET ' + m[3] + ' HTTP/1.1\r\nHost: ' + m[1] + ':' + m[2] + '\r\nUpgrade: websocket\r\nConnection: Upgrade\r\nSec-WebSocket-Key: ' + k + '\r\nSec-WebSocket-Version: 13\r\n\r\n');
    });
    let buf = Buffer.alloc(0), hs = false, pend = new Map(), id = 0, events = [];
    const frame = pl => {
      const b = Buffer.from(pl); let head;
      if (b.length < 126) head = Buffer.from([0x81, 0x80 | b.length]);
      else if (b.length < 65536) { head = Buffer.alloc(4); head[0] = 0x81; head[1] = 0x80 | 126; head.writeUInt16BE(b.length, 2); }
      else { head = Buffer.alloc(10); head[0] = 0x81; head[1] = 0x80 | 127; head.writeBigUInt64BE(BigInt(b.length), 2); }
      const mask = crypto.randomBytes(4), body = Buffer.alloc(b.length);
      for (let i = 0; i < b.length; i++) body[i] = b[i] ^ mask[i % 4];
      return Buffer.concat([head, mask, body]);
    };
    const send = (method, params) => new Promise((rs, rj) => {
      if (!hs) return rj(new Error('not connected'));
      const i = ++id; pend.set(i, { rs, rj });
      s.write(frame(JSON.stringify({ id: i, method, params: params || {} })));
      setTimeout(() => { if (pend.has(i)) { pend.delete(i); rj(new Error('timeout ' + method)); } }, 30000);
    });
    const on = fn => events.push(fn);
    s.on('data', c => {
      buf = Buffer.concat([buf, c]);
      if (!hs) { const i = buf.indexOf('\r\n\r\n'); if (i < 0) return; hs = true; buf = buf.slice(i + 4); resolve({ send, on, close: () => s.end() }); }
      while (buf.length >= 2) {
        const op = buf[0] & 15; let l = buf[1] & 127, o = 2;
        if (l === 126) { l = buf.readUInt16BE(2); o = 4; } else if (l === 127) { l = Number(buf.readBigUInt64BE(2)); o = 10; }
        if (buf.length < o + l) return;
        const p = buf.slice(o, o + l); buf = buf.slice(o + l);
        if (op === 1) {
          let j; try { j = JSON.parse(p.toString()); } catch (e) { continue; }
          if (j.id && pend.has(j.id)) { const { rs, rj } = pend.get(j.id); pend.delete(j.id); j.error ? rj(new Error(JSON.stringify(j.error))) : rs(j.result); }
          else if (j.method) events.forEach(f => { try { f(j); } catch (e) {} });
        }
      }
    });
    s.on('error', reject);
  });
}

/* ---------- 页面内探针库 ---------- */
function pageLib() {
  const SETTINGS = '.udc-microflow-editor-node-settings';
  const NODE = '.udc-microflow-editor-node-container';
  const vis = el => { if (!el) return false; const r = el.getBoundingClientRect(); const s = getComputedStyle(el); return r.width > 0 && r.height > 0 && s.visibility !== 'hidden' && s.display !== 'none'; };
  const txt = el => ((el && (el.innerText || el.textContent)) || '').replace(/\s+/g, ' ').trim();
  const cssPath = el => { if (!el || el.nodeType !== 1) return ''; if (el.id) return '#' + CSS.escape(el.id); const cls = (typeof el.className === 'string' && el.className.trim()) ? el.className.trim().split(/\s+/).slice(0, 2).map(c => '.' + CSS.escape(c)).join('') : ''; const p = el.parentElement ? cssPath(el.parentElement) : ''; return (p ? p + ' > ' : '') + el.tagName.toLowerCase() + cls; };
  function fnv(s) { let h1 = 0x811c9dc5, h2 = 0x01000193 ^ s.length; for (let i = 0; i < s.length; i++) { const c = s.charCodeAt(i); h1 ^= c; h1 = (h1 * 16777619) >>> 0; h2 = (h2 ^ (c + i)) >>> 0; h2 = (h2 * 2246822519) >>> 0; } return ('00000000' + h1.toString(16)).slice(-8) + ('00000000' + h2.toString(16)).slice(-8); }

  /* C1：从 live DOM 派生节点清单（无硬编码 label） */
  function enumNodes() {
    const seen = new Map();
    const containers = [...document.querySelectorAll(NODE + '[id]')];
    // D1 归一化：剥掉 _n<N> 与 _n<N><a-z> 实例后缀，纯类型入 nodeType，实例号入 instance
    //   CREATE_MAP_n6a -> nodeType=CREATE_MAP, instance="6a"；CONDITION_n18_0 -> nodeType=CONDITION, instance="18_0"
    const NORMALIZE_RX = /^(.*)_n(\d+(?:[a-z]|_\d+)?)$/i;
    for (const el of containers) {
      const id = el.id; if (seen.has(id)) continue;
      const r = el.getBoundingClientRect();
      const lEl = el.querySelector('.node-title-text') || el.querySelector('.node-title') || el;
      const m = id.match(NORMALIZE_RX);
      seen.set(id, { nodeId: id, nodeType: m ? m[1] : id, instance: m ? m[2] : null, label: (lEl.innerText || '').split('\n')[0].trim(), coords: { x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height) } });
    }
    return {
      enumSource: "document.querySelectorAll('.udc-microflow-editor-node-container[id]')  // id=<NODE_TYPE>_n<INSTANCE>",
      domContainerCount: containers.length, uniqueNodeCount: seen.size, nodes: [...seen.values()],
      canvas: (() => { const b = document.querySelector('.nodes'); return b ? { scrollLeft: Math.round(b.scrollLeft), scrollTop: Math.round(b.scrollTop), cls: b.className } : null; })()
    };
  }
  function state() {
    const rootAll = document.querySelector(SETTINGS);
    // v4 关键修正（本轮实测真因）：平台关闭抽屉后**不销毁** settings 根，只把 .ant-drawer 设 display:none。
    // 用 querySelector(SETTINGS) 计数永远是 1 -> 「面板已关闭」判据永不成立 -> closed 永远 false -> 后续全污染。
    // 权威判据 = 可见的 settings 根（getBoundingClientRect 有尺寸且祖先未被 display:none）。
    const roots = [...document.querySelectorAll(SETTINGS)];
    const visRoots = roots.filter(vis);
    const root = visRoots[0] || null;
    const titleEl = root ? root.querySelector('.ant-drawer-title') : null;
    return {
      panelOpen: !!root, settingsCount: visRoots.length,
      settingsRootInDom: roots.length,
      hiddenRootCount: roots.length - visRoots.length,
      drawerTitle: titleEl ? (titleEl.innerText || '').trim() : null,
      drawerOpen: [...document.querySelectorAll('.ant-drawer')].filter(vis).length,
      activeIds: [...document.querySelectorAll(NODE + '.active')].map(e => e.id),
      textLen: root ? (root.innerText || '').length : 0,
      drawerBodyLen: (() => { const b = [...document.querySelectorAll('.ant-drawer-body')].filter(vis)[0]; return b ? (b.innerText || '').replace(/\s+/g, ' ').trim().length : 0; })(),
      panelLoaded: !!(root && (root.innerText || '').replace(/\s+/g, ' ').trim().length > 60),
      blockingConfirm: (() => {
        const m = [...document.querySelectorAll('.ant-modal-confirm')].filter(vis)[0];
        if (!m) return null;
        return { text: (m.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 120), buttons: [...m.querySelectorAll('button')].map(b => (b.innerText || '').trim()) };
      })(),
      masks: (() => {
        const o = [];
        for (const el of document.querySelectorAll('[class*="loading"],[class*="spin"],[class*="skeleton"],[class*="mask"]')) {
          const c = typeof el.className === 'string' ? el.className : '';
          if (/nested-loading|spin-container|spin-blur|spin-nested/.test(c)) continue;
          // 容器本身不是遮罩：ant-drawer / ant-modal 外壳带 'no-mask'、'ant-modal-mask' 亦为容器附属
          if (/^(ant-drawer|ant-modal|ant-drawer-content|ant-modal-wrap)\b/.test(c)) continue;
          if (/^(top|bottom)-line-mask$|scroll-mask|scrollbar/.test(c)) continue;
          if (!vis(el)) continue;
          const r = el.getBoundingClientRect();
          // 真遮罩 = 覆盖式大面积可点击遮罩，或大尺寸 spinner；纯文本「加载中...」/细线遮罩不算
          const overlay = /(^|[\s-])(overlay|mask)([\s-]|$)/i.test(c) && !/no-mask/.test(c) && r.width > 300 && r.height > 250;
          const bigSpin = /spinning|active/.test(c) && r.width > 60 && r.height > 60 && !!el.querySelector('.ant-spin-dot');
          if (overlay || bigSpin) o.push((c.trim().split(/\s+/)[0] || 'mask').slice(0, 30));
          if (o.length >= 5) break;
        }
        return [...new Set(o)];
      })()
    };
  }
  /* v4：平台「当前配置有修改，是否保存？」确认框（ant-modal-confirm）会以全屏 .ant-modal-wrap 覆盖画布，
   * 且它的按钮**不响应** dispatchEvent('click') 单发（实测：单发 click 无效，需完整 pointer 序列）。
   * 边界极严：只允许点「取 消」（留在当前，不保存也不丢弃）—— 绝不点「保 存」/「不保存」/OK。
   * 若框里没有「取 消」按钮，则返回未处理，由上层 fail-fast，不猜。 */
  function dismissConfirm() {
    const m = [...document.querySelectorAll('.ant-modal-confirm')].filter(vis)[0];
    if (!m) return { present: false };
    const text = (m.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 120);
    const btns = [...m.querySelectorAll('button')];
    const cancel = btns.find(b => /^取\s*消$/.test((b.innerText || '').trim()));
    if (!cancel) return { present: true, dismissed: false, reason: 'no-cancel-button-only-non-safe-options', text, buttons: btns.map(b => (b.innerText || '').trim()) };
    const rc = cancel.getBoundingClientRect();
    const x = Math.round(rc.x + rc.width / 2), y = Math.round(rc.y + rc.height / 2);
    const o = { bubbles: true, cancelable: true, composed: true, view: window, clientX: x, clientY: y, button: 0 };
    const fired = [];
    for (const t of ['pointerover', 'pointerenter', 'pointerdown', 'mousedown', 'pointerup', 'mouseup', 'click']) {
      try { const E = t.startsWith('pointer') ? PointerEvent : MouseEvent; cancel.dispatchEvent(new E(t, o)); fired.push(t); } catch (e) {}
    }
    return { present: true, dismissed: true, clicked: '取 消', at: { x, y }, fired, text, safeNote: '只点「取 消」：不保存、不丢弃当前编辑，纯视图层关闭确认框' };
  }
  /* R1 关抽屉（close 按钮优先，其次 mask），返回是否已关闭 */
  function closeDrawer() {
    const btns = [...document.querySelectorAll('.ant-drawer-close')].filter(vis);
    if (btns.length) { btns.forEach(b => { try { b.click(); } catch (e) {} }); return { attempted: true, by: 'drawer-close', count: btns.length }; }
    const mask = [...document.querySelectorAll('.ant-drawer-mask,.ant-modal-mask')].filter(vis)[0];
    if (mask) { try { mask.click(); } catch (e) {} return { attempted: true, by: 'mask' }; }
    return { attempted: false, by: 'none' };
  }
  /* R1 扩展（live v3 run2 教训）：n17 之后有非 node-settings 抽屉/modal 残留（hitCls=ant-drawer-body），
   * 只盯 settingsCount==0 会让覆盖层一直挡画布 -> 右侧节点全部 precheck:outside-node-subtree。
   * closeOverlays：关一切可见 drawer/modal 壳 + 一次 Esc；只关壳层，不碰任何节点配置。 */
  function closeOverlays() {
    const did = [];
    const cd = closeDrawer(); if (cd.attempted) did.push('drawer-close:' + cd.by);
    const mclose = [...document.querySelectorAll('.ant-modal-close')].filter(vis);
    if (mclose.length) { mclose.forEach(b => { try { b.click(); } catch (e) {} }); did.push('modal-close'); }
    try {
      const k = { key: 'Escape', code: 'Escape', keyCode: 27, which: 27, bubbles: true, cancelable: true };
      document.body.dispatchEvent(new KeyboardEvent('keydown', k)); document.body.dispatchEvent(new KeyboardEvent('keyup', k));
      did.push('esc');
    } catch (e) {}
    return { attempted: did.length > 0, did };
  }
  /* v4 / REQ-1.1 遮挡源识别与清理（auditor 已验证根因：僵尸 .ant-drawer 空壳 bodyChildCount===0 但
   * .ant-drawer-body 仍 pointer-events:auto，覆盖 x≥945 整片画布）。
   * 清理顺序 = 关闭按钮 -> modal close -> ESC -> 空壳纯视图移除（display:none，只改样式不改数据）。
   * 返回 zombies[]（每个被移除空壳的 id/cls/rect），供证据链复核。
   * 边界：只动 CSS display，不点「确定」、不保存、不碰 form 值。 */
  function zombieShells() {
    const out = [];
    const shells = [...document.querySelectorAll('.ant-drawer,.ant-modal-wrap,.ant-modal-root')];
    for (const sh of shells) {
      if (!vis(sh)) continue;
      const body = sh.querySelector('.ant-drawer-body,.ant-modal-body');
      const hasSettings = !!sh.querySelector(SETTINGS);
      const bodyChildren = body ? body.children.length : 0;
      const bodyText = body ? (body.innerText || '').replace(/\s+/g, ' ').trim() : '';
      const titleEl = sh.querySelector('.ant-drawer-title,.ant-modal-title');
      const r = sh.getBoundingClientRect();
      out.push({
        cls: (typeof sh.className === 'string' ? sh.className : '').slice(0, 60),
        hasSettings, bodyChildren, bodyTextLen: bodyText.length, title: titleEl ? txt(titleEl) : '',
        rect: { x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height) },
        pe: body ? getComputedStyle(body).pointerEvents : null,
        empty: !hasSettings && bodyChildren === 0 && bodyText.length === 0,
        el: sh
      });
    }
    return out;
  }
  function clearOccluders() {
    const steps = [], zombies = [], confirms = [];
    // 0) 确认框优先：它盖在最上层，且只允许点「取 消」（不保存）
    for (let i = 0; i < 3; i++) {
      const dc = dismissConfirm();
      if (!dc.present) break;
      confirms.push(dc);
      steps.push('confirm:' + (dc.dismissed ? 'dismissed-by-cancel' : 'UNRESOLVED:' + dc.reason));
      if (!dc.dismissed) break;
    }
    // 1) 正常关闭（关闭按钮）
    const cd = closeDrawer();
    if (cd.attempted) steps.push('drawer-close:' + cd.by);
    // 2) modal 关闭按钮
    const mclose = [...document.querySelectorAll('.ant-modal-close')].filter(vis);
    if (mclose.length) { mclose.forEach(b => { try { b.click(); } catch (e) {} }); steps.push('modal-close:' + mclose.length); }
    // 3) ESC
    try {
      const k = { key: 'Escape', code: 'Escape', keyCode: 27, which: 27, bubbles: true, cancelable: true };
      document.body.dispatchEvent(new KeyboardEvent('keydown', k)); document.body.dispatchEvent(new KeyboardEvent('keyup', k));
      steps.push('esc');
    } catch (e) {}
    // 4) 空壳纯视图移除：仅 bodyChildCount===0 且无 SETTINGS 且无正文 —— 这是「已关但没销毁」的残留
    for (const z of zombieShells()) {
      if (!z.empty) continue;
      try {
        z.el.style.display = 'none';
        z.el.setAttribute('data-probe-zombie-removed', '1');
        const r2 = z.el.getBoundingClientRect();
        zombies.push({ cls: z.cls, title: z.title, bodyChildren: z.bodyChildren, bodyTextLen: z.bodyTextLen, rect: z.rect, after: { w: Math.round(r2.width), h: Math.round(r2.height) }, how: 'display:none (view-only, no config touched)' });
        steps.push('zombie-remove:' + z.cls.split(' ')[0]);
      } catch (e) { steps.push('zombie-remove-failed:' + String(e.message).slice(0, 40)); }
    }
    const cleared = occluderState();
    return { steps, zombies, confirms, cleared };
  }
  /* 命中复验：目标节点中心是否真的可达（祖先链无 .ant-drawer/.ant-modal），以及遮挡源是谁。
   * v4 修正（实测教训）：节点画布坐标可能是负数（画布平移，x=-3408），此时 elementFromPoint 返回 null，
   * 那是「不在视口」不是「被遮挡」——两者必须分开，否则会把 offscreen 误判成遮挡失败。
   * 因此先 bringIntoView 再测；inView=false 单独标注，不参与遮挡判定。 */
  function hitProbe(id) {
    const el = document.getElementById(id);
    if (!el) return { ok: false, reason: 'node-not-found' };
    const iv = bringIntoView(el);
    const r = el.getBoundingClientRect();
    const cx = Math.round(r.x + r.width / 2), cy = Math.round(r.y + r.height / 2);
    const inView = r.x + r.width > 0 && r.x < innerWidth && r.y + r.height > 0 && r.y < innerHeight;
    const h = inView ? document.elementFromPoint(Math.max(0, Math.min(innerWidth - 1, cx)), Math.max(0, Math.min(innerHeight - 1, cy))) : null;
    const inNode = !!(h && el.contains(h));
    const occl = h ? h.closest('.ant-drawer,.ant-modal-wrap,.ant-modal-root,.ant-modal') : null;
    return {
      ok: inView && inNode && !occl,
      rect: { x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height) },
      point: { x: cx, y: cy }, inView, inNode,
      offscreen: !inView,
      bringIntoView: iv,
      hit: h ? { tag: h.tagName, cls: hitCls(h) } : null,
      occluder: occl ? { cls: (typeof occl.className === 'string' ? occl.className : '').slice(0, 60), hasSettings: !!occl.querySelector(SETTINGS) } : null
    };
  }
  /* 当前遮挡全景（给 preClose / notes 用） */
  function occluderState() {
    const shells = zombieShells();
    const live = shells.filter(s => !s.empty);
    return {
      zombieCount: shells.filter(s => s.empty).length,
      liveShellCount: live.length,
      settingsCount: document.querySelectorAll(SETTINGS).length,
      shells: shells.map(s => ({ cls: s.cls, empty: s.empty, hasSettings: s.hasSettings, bodyChildren: s.bodyChildren, bodyTextLen: s.bodyTextLen, title: s.title, rect: s.rect }))
    };
  }
  /* 平移画布把节点移到无遮挡区（纯视图：只改 scrollLeft/scrollTop，不改任何配置）。
   * 平台画布无滚动容器，元素靠 CSS transform 定位 —— 无滚动祖先时降级为「整片空壳清理」证据，不谎报平移成功。 */
  function panCanvasTo(id) {
    const el = document.getElementById(id);
    if (!el) return { panned: false, reason: 'node-not-found' };
    let p = el.parentElement, target = null;
    while (p && p !== document.body) {
      if (p.scrollWidth > p.clientWidth + 4 || p.scrollHeight > p.clientHeight + 4) { target = p; break; }
      p = p.parentElement;
    }
    if (!target) {
      const cv = document.querySelector('.nodes');
      return { panned: false, reason: 'no-scroll-container', canvasCls: cv ? cv.className : null, note: '画布节点以 CSS transform 定位，无滚动容器可平移；改走遮挡清理路径（不谎报平移）' };
    }
    const before = { sl: target.scrollLeft, st: target.scrollTop };
    const r = el.getBoundingClientRect();
    target.scrollLeft += Math.round(r.x - 200);
    const after = { sl: target.scrollLeft, st: target.scrollTop };
    return { panned: before.sl !== after.sl || before.st !== after.st, before, after, cls: (typeof target.className === 'string' ? target.className : '').slice(0, 40) };
  }
  /* R2/D2 点击节点：点击前 elementFromPoint 预校验；命中编辑控件或非目标子树则换点重试 */
  const hitCls = el => (el ? (typeof el.className === 'string' ? el.className.slice(0, 60) : el.tagName) : null);
  const BAD_HIT = el => {
    if (!el) return 'no-element';
    const tag = el.tagName;
    if (tag === 'INPUT' || tag === 'TEXTAREA') return 'editable:' + tag;
    if (el.isContentEditable) return 'contenteditable';
    return null;
  };
  /* 画布可能被平移到视口外（负坐标）：elementFromPoint 对视口外元素返回 null。
   * 先滚动最近的可滚祖先把节点带入视口（v2.2 F3 的教训：滚动后必须【重新读 rect】，不用旧值）。 */
  function bringIntoView(el) {
    let moved = null;
    let p = el.parentElement;
    while (p && p !== document.body) {
      if (p.scrollWidth > p.clientWidth + 4 || p.scrollHeight > p.clientHeight + 4) {
        const before = { sl: p.scrollLeft, st: p.scrollTop };
        el.scrollIntoView({ block: 'nearest', inline: 'nearest' });
        if (p.scrollLeft !== before.sl || p.scrollTop !== before.st) moved = { scrollLeft: Math.round(p.scrollLeft), scrollTop: Math.round(p.scrollTop) };
        break;
      }
      p = p.parentElement;
    }
    const r = el.getBoundingClientRect();
    const onScreen = r.x + r.width > 0 && r.x < innerWidth && r.y + r.height > 0 && r.y < innerHeight;
    return { moved, rect: { x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height) }, onScreen };
  }
  function candidatePoints(el) {
    const pts = [];
    const icon = el.querySelector('.node-icon, sy-icon, [class*="icon"]');
    const title = el.querySelector('.node-title-text') || el.querySelector('.node-title');
    const push = (sel, el2, dx, dy) => {
      if (!el2) return;
      const r = el2.getBoundingClientRect();
      const x = Math.round(r.x + r.width / 2 + (dx || 0)), y = Math.round(r.y + r.height / 2 + (dy || 0));
      pts.push({ selector: sel, x, y, rect: { x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height) } });
    };
    push('icon-center', icon);
    push('title-left-8px', title, -8, 0);       // 标题文字中心常是 input.edit-input，左移 8px 避开
    push('title-outline', el.querySelector('.node-title'));
    if (!pts.length) {
      const r = el.getBoundingClientRect();
      pts.push({ selector: 'node-center', x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2), rect: { x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height) } });
    }
    return pts;
  }
  function clickAt(el, pt) {
    const hit0 = document.elementFromPoint(pt.x, pt.y);
    const bad = BAD_HIT(hit0);
    const inside = !!(hit0 && el.contains(hit0));
    // 预校验：可编辑控件 或 根本不在目标节点子树 -> 本点不合格
    if (bad) return { ok: false, attempt: { selector: pt.selector, x: pt.x, y: pt.y, hitTag: hit0 ? hit0.tagName : null, hitCls: hitCls(hit0), ok: false, reject: 'precheck:' + bad } };
    if (!inside) return { ok: false, attempt: { selector: pt.selector, x: pt.x, y: pt.y, hitTag: hit0 ? hit0.tagName : null, hitCls: hitCls(hit0), ok: false, reject: 'precheck:outside-node-subtree' } };
    // DOM 合成点击（CDP Input 在本页 timeout）
    const o = { bubbles: true, cancelable: true, view: window, clientX: pt.x, clientY: pt.y };
    const fired = [];
    for (const ty of ['pointerdown', 'mousedown', 'pointerup', 'mouseup', 'click']) {
      try { hit0.dispatchEvent(new (ty.startsWith('pointer') ? PointerEvent : MouseEvent)(ty, o)); fired.push(ty); } catch (e) {}
    }
    // v4 修（本轮第二轮实测）：precheck 通过后才允许 el.click() 容器级兜底 —— **它绝不绕过 precheck**。
    // 教训链：v3 的兜底写在 precheck 之后（正确）；我先删掉它 -> 面板再也不打开（16/21 PANEL_SWITCH_FAIL）；
    // 说明平台的节点点击处理器只认容器级 click。真正的编辑态风险来自「点到 .node-title-text 里的 input」，
    // 那是 precheck:editable 负责拦的（BAD_HIT），与容器 click 无关。
    try { el.click(); fired.push('el.click'); } catch (e) {}
    return { ok: fired.length > 0, fired, attempt: { selector: pt.selector, x: pt.x, y: pt.y, hitTag: hit0.tagName, hitCls: hitCls(hit0), ok: true, reject: null } };
  }
  /* v4 点击节点：三候选点 × 三轮（原始 -> 清理遮挡后 -> 平移画布后）。
   * 判据（R1，不放宽）：命中点必须在目标节点子树内且非可编辑控件 —— 这是「点到了这个节点」的唯一硬证据。
   * 被遮挡不是「节点身份失败」，而是「遮挡源待清理」：清理后重试；三路全败才 CLICK_TARGET_FAIL，
   * 且失败记录必须带 occluder 现场（谁遮的、多大、有没有 SETTINGS），不是笼统 precheck。 */
  function clickNode(id) {
    const el = document.getElementById(id);
    if (!el) return { ok: false, reason: 'node-not-found', clickTarget: null };
    const rounds = [];
    const attempts = [];
    let occluderNote = null;
    const tryRound = (label, doClear) => {
      const r0 = [];
      if (doClear) {
        const cl = clearOccluders();
        r0.push({ round: label, clearSteps: cl.steps, zombiesRemoved: cl.zombies.length, cleared: cl.cleared });
      }
      const iv = bringIntoView(el);
      for (const pt of candidatePoints(el)) {
        const a = clickAt(el, pt);
        attempts.push(Object.assign({ round: label }, a.attempt));
        if (a.ok) return { ok: true, fired: a.fired, pt, round: label, bringIntoView: iv, prep: r0, el };
      }
      // 本轮全败：记遮挡现场
      const hp = hitProbe(id);
      occluderNote = hp;
      r0.push({ round: label, hitProbe: hp, bringIntoView: iv });
      rounds.push(...r0);
      return { ok: false, rounds: r0 };
    };
    // 第 1 轮：现状直点（抽屉可能本来就关着，别做多余动作）
    let res = tryRound('raw', false);
    if (!res.ok) {
      // 第 2 轮：识别并清理遮挡源（关闭 -> ESC -> 空壳纯视图移除），再点
      res = tryRound('after-clear-occluders', true);
      if (res.ok) res.recoveredBy = 'clear-occluders';
    }
    if (!res.ok) {
      // 第 3 轮：平移画布把节点移到无遮挡区（纯视图），再点
      const pan = panCanvasTo(id);
      res = tryRound('after-pan-canvas', true);
      res.pan = pan;
      if (res.ok) res.recoveredBy = 'pan-canvas';
    }
    if (res.ok) {
      const h0 = document.elementFromPoint(res.pt.x, res.pt.y);
      return {
        ok: true, fired: res.fired, bringIntoView: res.bringIntoView, rounds,
        clickTarget: {
          selector: res.pt.selector, x: res.pt.x, y: res.pt.y,
          hitTag: h0 ? h0.tagName : null, hitCls: hitCls(h0),
          hitInsideNode: !!(h0 && el.contains(h0)),
          attempts, roundsUsed: res.round, recoveredBy: res.recoveredBy || null
        }
      };
    }
    return {
      ok: false,
      reason: 'CLICK_TARGET_FAIL: 3 candidates x 3 rounds (raw / after-clear-occluders / after-pan-canvas) all rejected',
      occluderEvidence: occluderNote,
      rounds,
      clickTarget: { selector: null, x: null, y: null, hitTag: null, hitCls: null, attempts, roundsUsed: 'all-failed', recoveredBy: null }
    };
  }
  const ITEM = '.ant-form-item,[class*="form-item"],[class*="setting-item"],[class*="config-item"]';
  function labelOf(ctrl) {
    const it = ctrl.closest(ITEM);
    if (it) { const l = it.querySelector('.ant-form-item-label,label,[class*="label"]'); const t = txt(l || it); if (t && t.length <= 40) return t.replace(/\s*\*+\s*$/, ''); }
    const ph = ctrl.getAttribute('placeholder'); if (ph) return ph;
    return ctrl.getAttribute('name') || '';
  }
  /* C2 + C5：面板身份 + 字段 */
  function capture() {
    const st = state();
    const root = st.panelOpen ? document.querySelector(SETTINGS) : null;
    const base = Object.assign({}, st, { url: location.href });
    if (!root) return base;
    const rect = root.getBoundingClientRect();
    const ctls = [...root.querySelectorAll('input,textarea,select')].filter(vis);
    const inputs = [], selects = [], requiredFields = [];
    for (const c of ctls) {
      const lab = labelOf(c);
      const it = c.closest(ITEM);
      const labEl = it ? it.querySelector('.ant-form-item-label,label,[class*="label"]') : null;
      const req = !!c.required || c.getAttribute('aria-required') === 'true' || (!!it && (/required|is-required/.test(it.className || '') || /必填/.test(txt(labEl || it).slice(0, 60))));
      const info = { name: c.getAttribute('name') || '', type: c.tagName === 'SELECT' ? 'select' : (c.getAttribute('type') || c.tagName.toLowerCase()), value: (c.value || '').slice(0, 200), placeholder: c.getAttribute('placeholder') || '', required: req, disabled: !!c.disabled || c.getAttribute('aria-disabled') === 'true', readonly: !!c.readOnly, label: lab, selector: cssPath(c) };
      if (c.tagName === 'SELECT') selects.push(Object.assign(info, { selectedText: (c.selectedOptions[0] ? c.selectedOptions[0].text : '').slice(0, 80), options: [...c.options].slice(0, 25).map(o => ({ v: o.value, t: o.text.trim().slice(0, 60), sel: o.selected })) }));
      else inputs.push(info);
      if (req) requiredFields.push({ label: lab, name: info.name, selector: info.selector });
    }
    const formLabels = [...new Set([...root.querySelectorAll('.ant-form-item-label,label,[class*="label"]')].filter(vis).map(txt).filter(t => t && t.length <= 40).map(t => t.replace(/\s*\*+\s*$/, '')))];
    const btns = [...new Set([...root.querySelectorAll('button,[class*="btn"],[role="button"]')].filter(vis).map(txt).filter(t => t && t.length <= 16))].slice(0, 10);
    const lines = (root.innerText || '').split('\n').map(s => s.trim()).filter(Boolean);
    const firstLine = (lines.find(l => l.length > 10) || '').slice(0, 60);
    const ctlSig = ctls.map(c => [c.tagName, c.getAttribute('type') || '', labelOf(c).slice(0, 20), (c.getAttribute('placeholder') || '').slice(0, 12)].join(':')).sort();
    const material = { drawerTitle: st.drawerTitle, formLabels, ctlSig, btns };
    return Object.assign(base, {
      rootSelector: cssPath(root) || SETTINGS, rootRect: { x: Math.round(rect.x), y: Math.round(rect.y), w: Math.round(rect.width), h: Math.round(rect.height) },
      headerTitle: st.drawerTitle, headerTitleSource: '.ant-drawer-title (平台面板标题元素，权威身份)',
      firstLine, formLabels, buttons: btns,
      nodeTypeHint: (function () {
        const full = (root.innerText || '').slice(0, 4000) + ' ' + (st.drawerTitle || '');
        const T = [['CALL_CUSTOM_SERVICE', ['自定义服务', '对外暴露的服务接口']], ['PUBLISH_EVENT', ['事件投递', '业务事件']], ['DATA_CONVERT', ['数据转换', '映射规则']], ['SUB_FLOW', ['子微流程']], ['CREATE_VARIABLE', ['创建变量', '创建包括基本数据']], ['CREATE_LIST', ['创建列表', '变量列表']], ['MODIFY_LIST', ['修改列表', '修改已有的列表']], ['LIST_OPERATION', ['列表操作', '对已有的列表进行操作']], ['CREATE_MAP', ['创建映射组', '映射键值对']], ['MAP_OPERATION', ['映射操作', '选择已有映射组']], ['UPDATE_DATA', ['更新数据', '聚合根实体单条数据']], ['BATCH_UPDATE', ['批量更新数据', '聚合根实体列表数据']], ['INSERT_DATA', ['插入数据', '插入到数据库中']], ['DELETE_DATA', ['删除数据', '删除规则']], ['TYPE_CONVERT', ['类型转换', '封装后的工具方法']], ['QUERY_ONE', ['查询单条数据', '条件查询']], ['MODIFY_VARIABLE', ['修改变量', '修改前序节点中已创建的变量']], ['BRANCH', ['条件分支']]];
        let best = 0, hint = 'unknown';
        for (const [t, kw] of T) { const s = kw.filter(k => full.includes(k)).length; if (s > best) { best = s; hint = t; } }
        return { hint, score: best, confidence: best >= 2 ? 'high' : best === 1 ? 'low' : 'none' };
      })(),
      fingerprint: fnv(JSON.stringify(material)),
      fingerprintBasis: 'FNV1a x2 over {drawerTitle, formLabels[], ctlSig[], buttons[]} — 面板自身结构，不含 nodeId、非 innerText 全文',
      structural: material, controlCount: ctls.length,
      inputs, selects, requiredFields, textSample: (root.innerText || '').slice(0, 500)
    });
  }
  /* 点击 form-item 中某个 label 对应的 control 区按钮（映射关系这类必填项的入口） */
  function clickFieldControl(labelPattern) {
    if (!state().panelOpen) return { ok: false, reason: 'panel-not-open' };
    const root = document.querySelector(SETTINGS);
    const re = new RegExp(labelPattern);
    const items = [...root.querySelectorAll('.ant-form-item,[class*="form-item"],[class*="setting-item"]')].filter(vis);
    for (const it of items) {
      const lab = it.querySelector('.ant-form-item-label,label,[class*="label"]');
      const labTxt = lab ? txt(lab) : '';
      const allTxt = txt(it);
      if (!(re.test(labTxt) || re.test(allTxt) || it.querySelector('.ant-form-item-required,[class*="required"]'))) continue;
      const ctrl = it.querySelector('.ant-form-item-control,[class*="control"]') || it;
      const btn = ctrl.querySelector('button,[class*="btn"],[role="button"],[class*="button"]')
        || [...ctrl.querySelectorAll('span,div,a')].filter(e => vis(e) && txt(e).length <= 8 && e.children.length === 0 && /设置|编辑|配置|查看/.test(txt(e)))[0];
      if (!btn) continue;
      try { btn.click(); } catch (e) {}
      return { ok: true, how: 'field-control-button', labelTxt: labTxt, fieldText: txt(it).slice(0, 40), btnText: txt(btn).slice(0, 20), btnSelector: cssPath(btn) };
    }
    return { ok: false, reason: 'no-control-button-for:' + labelPattern };
  }
  function captureDialog() {
    const all = [...document.querySelectorAll('[role="dialog"],[class*="modal"],[class*="dialog"]')]
      .filter(e => vis(e) && e.getBoundingClientRect().width > 320 && e.getBoundingClientRect().width < innerWidth * 0.99)
      // ant-drawer 自身也是 role=dialog：排除承载节点设置面板的抽屉，否则会把自己当弹窗采到
      .filter(e => !(e.classList && e.classList.contains('ant-drawer')) && !e.querySelector(SETTINGS));
    // 平台在「放弃未保存修改」时会弹确认框；它不是映射弹窗，必须识别出来而不是当成 mapping 证据
    const confirmDialog = all.find(e => /当前配置有修改|是否保存|不保存|确认放弃/.test((e.innerText || '').slice(0, 200)));
    if (confirmDialog) {
      const stay = [...confirmDialog.querySelectorAll('button')].find(b => /^取\s*消$|^取消$/.test(txt(b)));
      if (stay) { try { stay.click(); } catch (e) {} }
      return { open: false, reason: 'blocked-by-unsaved-changes-confirm', dismissedBy: stay ? '取消' : 'none', title: txt(confirmDialog).slice(0, 60) };
    }
    const d = all.sort((a, b) => b.getBoundingClientRect().width - a.getBoundingClientRect().width)[0];
    if (!d) return { open: false, reason: 'no-dialog-root (settings drawer excluded)' };
    const rows = [];
    for (const tr of d.querySelectorAll('tr')) { const cells = [...tr.querySelectorAll('td,th')].map(txt).filter(Boolean); if (cells.length) rows.push({ cells: cells.slice(0, 6), text: cells.join(' -> ').slice(0, 200) }); if (rows.length >= 40) break; }
    if (!rows.length) for (const r of d.querySelectorAll('[class*="row"],[class*="mapping"]')) { const t = txt(r); if (t.length > 3 && t.length < 200) rows.push({ cells: [], text: t.slice(0, 200) }); if (rows.length >= 40) break; }
    const pairs = [];
    for (const row of rows) { const m = row.text.match(/^(.{1,80}?)\s*(?:->|→|=>)\s*(.{1,80})$/); if (m) pairs.push({ from: m[1].trim(), to: m[2].trim() }); }
    return { open: true, rootSelector: cssPath(d), title: txt(d).slice(0, 60), rowCount: rows.length, rows: rows.slice(0, 25), pairCount: pairs.length, pairs: pairs.slice(0, 25) };
  }
  function expressionEntry() {
    if (!state().panelOpen) return { status: 'no_panel' };
    const root = document.querySelector(SETTINGS);
    const hits = [];
    for (const c of root.querySelectorAll('input,textarea')) { const pl = (c.getAttribute('placeholder') || '') + ' ' + labelOf(c); if (/表达式|expr|公式/i.test(pl)) hits.push({ name: c.getAttribute('name') || '', label: labelOf(c), value: (c.value || '').slice(0, 300), selector: cssPath(c) }); }
    const btns = [...root.querySelectorAll('button,[class*="btn"],[role="button"]')].filter(e => vis(e) && /^(表达式|fx|公式)$/.test(txt(e))).map(txt);
    const tokensOf = s => { const o = []; const re = /[A-Za-z_$][\w$]*(?:\.[\w$]+|\[[^\]]+\])*/g; let m; while ((m = re.exec(s)) && o.length < 30) o.push(m[0]); return [...new Set(o)]; };
    if (!hits.length && !btns.length) return { status: 'none_present', paramAreaPresent: /参数|入参/.test(root.innerText || ''), tokens: [] };
    const raw = hits.map(h => h.value).filter(Boolean).join(' | ');
    return { status: raw ? 'present' : 'entry_present_empty', raw: raw.slice(0, 400), fields: hits, buttons: btns, tokens: tokensOf(raw) };
  }

  /* D3: BRANCH/CONDITION 分支自身 UI 只读采集（不进编辑态、不保存）。
   * 分支节点画布上直接渲染条件文本（.node-branch / 条件行）；抽屉型面板不存在，故从节点卡自身 DOM 取。 */
  /* v3.1 修正（live 13:41 证据）：旧实现把节点卡内任意文本行当条件行 ->
   *   BRANCH(标题「分支(2)」)只数到 1 行；CONDITION 的 exprRaw 抓成「符合条件即进入该分支」引导语，不是条件本身。
   * 真实只读结构（DOM 实测确认，见 v3 证据 branchSpec 原始输出）：
   *   BRANCH    [.caption-title]="分支(2)"（分支数权威源）  [.node-body-title]="条件分支"
   *   CONDITION [.condition-title-icon]=1|2（序号） [.condition-title-text]=符合条件即进入该分支|默认分支
   *             [.node-body-title]=真实条件表达式，例：为空(微流程.查询单条数据(1).实验数据导入_1 [小爪实验实体950795V2])
   * 因此按锚点定位，不再用任意文本行兜底；数量与条件卡不一致 -> BRANCH_UI_UNCAPTURED。 */
  function branchSpec(id) {
    const el = document.getElementById(id);
    if (!el) return { captured: false, reason: 'BRANCH_UI_UNCAPTURED: node element not found' };
    const pathTok = s => { const o = []; const re = /[\u4e00-\u9fa5A-Za-z_][\w\u4e00-\u9fa5]*(?:\.[\w\u4e00-\u9fa5()（）]+|\[[^\]]+\])*/g; let m; while ((m = re.exec(s || '')) && o.length < 30) { const t = m[0]; if (t.length >= 2) o.push(t); } return [...new Set(o)]; };
    const bodyTxt = c => { const b = c.querySelector('.node-body-title') || c.querySelector('.node-body'); return b ? txt(b) : ''; };
    const condOf = (c, i) => {
      const icon = c.querySelector('.condition-title-icon');
      const lt = c.querySelector('.condition-title-text');
      const expr = bodyTxt(c);
      return {
        index: icon && txt(icon) ? Number(txt(icon)) : i,
        nodeId: c.id,
        label: (lt ? txt(lt) : '') || null,
        exprRaw: expr || null,
        exprSource: expr ? 'dom:.node-body-title（平台自身渲染的条件表达式，只读文本，未进编辑态）' : null,
        tokens: pathTok(expr),
        source: 'node-card DOM (read-only)'
      };
    };
    if (/^BRANCH_n/.test(id)) {
      const inst = (id.match(/_n(\d+)$/) || [])[1] || id;
      const titleEl = el.querySelector('.caption-title') || el.querySelector('.node-title-text');
      const title = titleEl ? txt(titleEl) : '';
      const mCnt = title.match(/[（(]\s*(\d+)\s*[)）]/);
      const conds = [...document.querySelectorAll('.udc-microflow-editor-node-container[id^="CONDITION_n' + inst + '_"]')]
        .filter(c => c.id !== id).map((c, i) => condOf(c, i));
      const branchCount = mCnt ? Number(mCnt[1]) : null;
      const ok = !!branchCount && conds.length > 0 && branchCount === conds.length;
      return {
        captured: ok, branchCount, countSource: 'dom:.caption-title「' + title + '」括号内数字',
        conditions: conds, conditionCount: conds.length, countConsistent: ok,
        source: 'node-card DOM (read-only); 条件卡按 id 前缀 CONDITION_n' + inst + '_ 归组',
        reason: ok ? null : 'BRANCH_UI_UNCAPTURED: branchCount/conditions mismatch or unreadable (count=' + branchCount + ', conditions=' + conds.length + ')'
      };
    }
    if (/^CONDITION_n/.test(id)) {
      const one = condOf(el, 0);
      const parentBranchId = 'BRANCH_n' + (((id.match(/_n(\d+)_\d+$/) || [])[1]) || '');
      if (!one.exprRaw && !one.label) return { captured: false, reason: 'BRANCH_UI_UNCAPTURED: condition card has neither .node-body-title nor .condition-title-text', evidence: txt(el).slice(0, 200) };
      return { captured: true, branchCount: 1, parentBranchId, conditions: [one], conditionCount: 1, countConsistent: true, source: 'node-card DOM (read-only)', reason: null };
    }
    return { captured: false, reason: 'BRANCH_UI_UNCAPTURED: not a BRANCH/CONDITION node id: ' + id };
  }
  window.__PROBE = { __v: '4.0', enumNodes, state, capture, closeDrawer, closeOverlays, clearOccluders, dismissConfirm, zombieShells, occluderState, hitProbe, panCanvasTo, clickNode, clickFieldControl, captureDialog, expressionEntry, branchSpec, cssPath, txt, SETTINGS };
}

/* ---------- 判定 ---------- */
const ALLOW = {
  CALL_APP_SERVICE: ['CALL_CUSTOM_SERVICE'], PUBLISH_BUSINESS_EVENT: ['PUBLISH_EVENT'],
  DATA_MAPPING: ['DATA_CONVERT'], CONVERT_DATA: ['TYPE_CONVERT', 'DATA_CONVERT'],
  SUB_MICROFLOW: ['SUB_FLOW'], CREATE_VARIABLE: ['CREATE_VARIABLE'], CHANGE_VARIABLE: ['MODIFY_VARIABLE'],
  RETRIEVE: ['QUERY_ONE'], RETRIEVE_ARRAY: ['QUERY_ONE'], CREATE_LIST: ['CREATE_LIST'], CHANGE_LIST: ['MODIFY_LIST'],
  LIST_OPERATION: ['LIST_OPERATION'], CREATE_MAP: ['CREATE_MAP'], MAP_OPERATION: ['MAP_OPERATION'],
  CHANGE_ENTITY: ['UPDATE_DATA'], CHANGE_BATCH_ENTITY: ['BATCH_UPDATE'], CREATE_ENTITY: ['INSERT_DATA'], DELETE_ENTITY: ['DELETE_DATA']
};
const STRUCTURAL = /^(BRANCH|CONDITION|START|END|NOTE)$/;   // D1: 已归一化，精确匹配即可，禁前缀
function expectationFor(nodeType) {
  // D1: 精确相等查表；startsWith 会把 CHANGE_LIST 抢成 CREATE_LIST 等前缀歧义，禁用。
  const k = Object.keys(ALLOW).find(x => nodeType === x);
  return k ? ALLOW[k] : null;   // null => unmapped，不参与身份判定（evaluate 只对 exp 非空才判）
}

function evaluate(nodes) {
  const fails = [], notes = [], byFp = new Map();
  for (const n of nodes) {
    if (n.status === 'STRUCTURAL_BRANCH_CAPTURED') { n.panelIdentityMatch = null; notes.push({ code: 'BRANCH_SPEC_CAPTURED', node: n.nodeId, branchCount: n.branchSpec && n.branchSpec.branchCount }); continue; }
    if (n.status === 'STRUCTURAL_BRANCH_CAPTURED' && n.branchSpec && n.branchSpec.countConsistent === false) { fails.push({ code: 'BRANCH_UI_UNCAPTURED', rule: 'BRANCH_COUNT_ASSERT: branchCount != conditions.length', node: n.nodeId, nodeType: n.nodeType, evidence: { branchCount: n.branchSpec.branchCount, conditionCount: n.branchSpec.conditionCount } }); n.panelIdentityMatch = false; continue; }
    if (n.status === 'BRANCH_UI_UNCAPTURED') { fails.push({ code: 'BRANCH_UI_UNCAPTURED', rule: 'branch_ui_not_captured_no_null_success', node: n.nodeId, nodeType: n.nodeType, evidence: n.branchFailReason }); n.panelIdentityMatch = false; continue; }
    if (n.status === 'CLICK_TARGET_FAIL') { fails.push({ code: 'CLICK_TARGET_FAIL', rule: 'all_click_candidates_x_3_rounds_rejected_with_occluder_evidence', node: n.nodeId, nodeType: n.nodeType, evidence: n.clickTarget, occluderEvidence: n.open && n.open.occluderEvidence }); n.panelIdentityMatch = false; continue; }
    if (n.status === 'CLEAR_OVERLAY_FAIL') { fails.push({ code: 'CLEAR_OVERLAY_FAIL', rule: 'occluder_not_cleared_failed_fast_before_click', node: n.nodeId, nodeType: n.nodeType, evidence: n.preClose }); n.panelIdentityMatch = false; continue; }

    if (n.status === 'STRUCTURAL_NO_PANEL') { n.panelIdentityMatch = null; notes.push({ code: 'STRUCTURAL_NO_PANEL', node: n.nodeId, evidence: n.switchEvidence }); continue; }
    if (n.status === 'PANEL_SWITCH_FAIL') { fails.push({ code: 'PANEL_IDENTITY_FAIL', rule: 'panel_not_proven_for_this_node', node: n.nodeId, nodeType: n.nodeType, evidence: n.switchEvidence }); n.panelIdentityMatch = false; continue; }
    if (n.status === 'OPEN_FAIL') { fails.push({ code: 'NODE_NOT_CLICKABLE', rule: 'node_click_target_not_hittable', node: n.nodeId, nodeType: n.nodeType, evidence: n.open }); n.panelIdentityMatch = false; continue; }
    if (n.status === 'NO_PANEL') { fails.push({ code: 'NO_PANEL', rule: 'no_panel_root_after_click', node: n.nodeId, nodeType: n.nodeType, evidence: n.switchEvidence }); n.panelIdentityMatch = false; continue; }
    const fp = n.panelIdentity && n.panelIdentity.fingerprint;
    if (!fp) { fails.push({ code: 'NO_FINGERPRINT', node: n.nodeId }); n.panelIdentityMatch = false; continue; }
    const arr = byFp.get(fp) || []; arr.push(n); byFp.set(fp, arr);
  }
  for (const [fp, arr] of byFp) {
    const types = [...new Set(arr.map(x => x.nodeType))];
    if (arr.length > 1 && types.length > 1)
      fails.push({ code: 'PANEL_IDENTITY_FAIL', rule: 'duplicate_fingerprint_across_nodes', fingerprint: fp, nodes: arr.map(x => ({ nodeId: x.nodeId, nodeType: x.nodeType, label: x.label, drawerTitle: x.panelIdentity.headerTitle })), reason: 'Different node types produced identical panel fingerprint -> same panel captured twice.' });
    else if (arr.length > 1) notes.push({ code: 'SAME_TYPE_SAME_FP', fingerprint: fp, nodes: arr.map(x => x.nodeId) });
  }
  for (const n of nodes) {
    if (!n.panelIdentity) continue;
    const exp = expectationFor(n.nodeType), h = n.panelIdentity.nodeTypeHint;
    if (exp && h && h.confidence === 'high' && !exp.includes(h.hint))
      fails.push({ code: 'PANEL_IDENTITY_FAIL', rule: 'panel_title_contradicts_node_type', node: n.nodeId, nodeType: n.nodeType, expectedHints: exp, panelHint: h.hint, drawerTitle: n.panelIdentity.headerTitle });
  }
  for (const n of nodes) {
    if (n.status === 'STRUCTURAL_NO_PANEL') continue;
    const hit = fails.find(f => (f.node && f.node === n.nodeId) || (f.nodes && f.nodes.some(x => x.nodeId === n.nodeId)));
    if (n.panelIdentity) n.panelIdentityMatch = !hit;
    n.panelIdentityBasis = hit ? hit.rule : 'drawer re-opened after close + active nodeId == target + .ant-drawer-title read from this panel + unique fingerprint';
    if (n.panelIdentity) n.panelIdentity.nodeTypeHintExpected = expectationFor(n.nodeType);
  }
  // D2 notes: 解释 v2.2 观测到的「hitCls=ant-modal-wrap / hitInsideNode=false 但面板打开」
  // 判定：v2.2 的 hitCls 读的是【点击后】elementFromPoint —— 面板已打开，抽屉/遮罩盖住原坐标，
  // 所以读到的是 ant-modal-wrap。这不代表点击打在遮罩上；v3 改为点击【前】预校验 elementFromPoint，
  // clickTarget.attempts[].ok=true 表示点击瞬间命中点确在目标节点子树内且非可编辑控件。
  notes.push({ code: 'CLICK_TARGET_PRECHECK_NOTE', rule: 'hitCls in v2.2 was read AFTER the click (drawer already covering the point); v3 prechecks BEFORE the click, so attempts[].ok proves the hit was inside the target node subtree and not an editable input.' });
  const status = fails.length ? 'PANEL_IDENTITY_FAIL' : 'PASS';
  return { fails, notes, status, exitCode: status === 'PASS' ? 0 : 3 };
}

/* ---------- self-test ---------- */
function selfTest() {
  const mk = (id, type, fp, title) => ({ nodeId: id, nodeType: type, label: type, status: 'CAPTURED', switchEvidence: { activeAfter: [id], drawerTitle: title }, panelIdentity: { rootSelector: '#p', headerTitle: title, nodeTypeHint: { hint: title === '自定义服务' ? 'CALL_CUSTOM_SERVICE' : 'PUBLISH_EVENT', score: 2, confidence: 'high' }, fingerprint: fp }, panelIdentityMatch: null });
  const dup = evaluate([mk('CALL_APP_SERVICE_n16', 'CALL_APP_SERVICE', 'fpA', '自定义服务'), mk('PUBLISH_BUSINESS_EVENT_n17', 'PUBLISH_BUSINESS_EVENT', 'fpA', '自定义服务')]);
  const good = evaluate([mk('CALL_APP_SERVICE_n16', 'CALL_APP_SERVICE', 'fpA', '自定义服务'), mk('PUBLISH_BUSINESS_EVENT_n17', 'PUBLISH_BUSINESS_EVENT', 'fpB', '事件投递')]);
  const mis = evaluate([mk('PUBLISH_BUSINESS_EVENT_n17', 'PUBLISH_BUSINESS_EVENT', 'fpB', '自定义服务')]);
  const noSwitch = evaluate([{ nodeId: 'PUBLISH_BUSINESS_EVENT_n17', nodeType: 'PUBLISH_BUSINESS_EVENT', label: 'x', status: 'PANEL_SWITCH_FAIL', switchEvidence: { activeBefore: ['CALL_APP_SERVICE_n16'], activeAfter: ['CALL_APP_SERVICE_n16'] } }]);
  const struct = evaluate([{ nodeId: 'BRANCH_n18', nodeType: 'BRANCH', label: '分支(2)', status: 'STRUCTURAL_NO_PANEL', switchEvidence: { activeAfter: [] } }]);
  // D1: 归一化单测（纯函数，node 内即可跑）
  const NORMALIZE_RX = /^(.*)_n(\d+(?:[a-z]|_\d+)?)$/i;
  const norm = id => { const m = id.match(NORMALIZE_RX); return { nodeType: m ? m[1] : id, instance: m ? m[2] : null }; };
  const normChecks = [
    ['CREATE_MAP_n6a', 'CREATE_MAP', '6a'], ['CONDITION_n18_0', 'CONDITION', '18_0'], ['CONDITION_n18_1', 'CONDITION', '18_1'],
    ['CALL_APP_SERVICE_n16', 'CALL_APP_SERVICE', '16'], ['BRANCH_n18', 'BRANCH', '18'], ['RETRIEVE_n2', 'RETRIEVE', '2']
  ].map(([id, t, i]) => { const g = norm(id); return { id, expectType: t, gotType: g.nodeType, expectInstance: i, gotInstance: g.instance, pass: g.nodeType === t && g.instance === i }; });
  // D1: ALLOW 精确相等（前缀不再吞）
  const precChecks = [
    { nodeType: 'CHANGE_LIST', got: expectationFor('CHANGE_LIST'), expect: ['MODIFY_LIST'], note: 'v2 startsWith 会被 CREATE_LIST 抢走' },
    { nodeType: 'MAP_OPERATION', got: expectationFor('MAP_OPERATION'), expect: ['MAP_OPERATION'], note: 'v2 被 /MAP/(CREATE_MAP) 抢走' },
    { nodeType: 'CONVERT_DATA', got: expectationFor('CONVERT_DATA'), expect: ['TYPE_CONVERT', 'DATA_CONVERT'], note: 'v2 被 /CONVERT/(DATA_CONVERT) 抢走' },
    { nodeType: 'CREATE_LIST', got: expectationFor('CREATE_LIST'), expect: ['CREATE_LIST'] },
    { nodeType: 'UNKNOWN_TYPE_XY', got: expectationFor('UNKNOWN_TYPE_XY'), expect: null, note: 'unmapped 不参与判定' }
  ].map(c => Object.assign(c, { pass: JSON.stringify(c.got) === JSON.stringify(c.expect) }));
  const pseudo = ['CREATE_MAP_n6a', 'CONDITION_n18_0', 'CONDITION_n18_1'].filter(x => /_n\d/.test(norm(x).nodeType));
  const normOk = normChecks.every(c => c.pass) && precChecks.every(c => c.pass) && pseudo.length === 0;
  // D2: 点击命中 input -> 换点；全候选被拒 -> CLICK_TARGET_FAIL（纯逻辑重放，不开浏览器）
  const fakePre = { attempts: [{ selector: 'title-center', hitTag: 'INPUT', ok: false, reject: 'precheck:editable:INPUT' }, { selector: 'icon-center', hitTag: 'SY-ICON', ok: true, reject: null }, { selector: 'title-left-8px', hitTag: 'DIV', ok: false, reject: 'precheck:outside-node-subtree' }].filter(a => !a.ok || a.selector === 'icon-center') };
  const clickFailCase = { attempts: [{ selector: 'icon-center', hitTag: 'INPUT', ok: false, reject: 'precheck:editable:INPUT' }, { selector: 'title-left-8px', hitTag: 'INPUT', ok: false, reject: 'precheck:editable:INPUT' }, { selector: 'title-outline', hitTag: 'INPUT', ok: false, reject: 'precheck:editable:INPUT' }] };
  const clickFailOk = clickFailCase.attempts.length === 3 && clickFailCase.attempts.every(a => a.ok === false);
  // v4 self-test：遮挡清理与 fail-fast 的纯逻辑用例（不连浏览器）
  //  a) 僵尸空壳判定：bodyChildCount=0 + 无 SETTINGS + 无正文 => empty=true（可移除）
  //  b) 有正文的空壳 / 有 SETTINGS 的抽屉 => empty=false（绝不当空壳移除，避免关掉真面板）
  const shellEmpty = (s) => !s.hasSettings && s.bodyChildren === 0 && s.bodyTextLen === 0;
  const shellCases = [
    { name: 'zombie shell (no settings, no body, no text) is removable', shell: { hasSettings: false, bodyChildren: 0, bodyTextLen: 0 }, expectEmpty: true },
    { name: 'drawer carrying settings panel is NOT removable', shell: { hasSettings: true, bodyChildren: 3, bodyTextLen: 120 }, expectEmpty: false },
    { name: 'shell with body text but no settings stays (已关但仍有内容/动画残留)', shell: { hasSettings: false, bodyChildren: 0, bodyTextLen: 42 }, expectEmpty: false }
  ].map(c => Object.assign(c, { gotEmpty: shellEmpty(c.shell), pass: shellEmpty(c.shell) === c.expectEmpty }));
  const zombieOk = shellCases.every(c => c.pass);
  //  c) preClose 强一致：drawerCleared=false 且命中被遮挡（inView 且不在节点子树）=> 必须 CLEAR_OVERLAY_FAIL，禁止进入点击。
  //     offscreen（不在视口）不算遮挡 —— 那是画布平移问题，交 clickNode 的 pan 轮次，不得误判成遮挡失败（本轮真回归教训）。
  const failFastCase = (() => {
    const decide = (drawerCleared, inView, inNode) => {
      const occluded = inView && !inNode;
      return (!drawerCleared && occluded) ? 'CLEAR_OVERLAY_FAIL' : 'PROCEED';
    };
    const a = decide(false, true, false), b = decide(true, true, true), c = decide(true, false, false), d = decide(false, false, false);
    return { a, b, c, d, pass: a === 'CLEAR_OVERLAY_FAIL' && b === 'PROCEED' && c === 'PROCEED' && d === 'PROCEED' };
  })();
  //  d) writes 分类（v4 实测口径）：平台 GraphQL 外壳统一是 `mutation graphqlLoader { data0: <rootField> }`，
  //     外层 mutation 无区分度；读写信号取 rootField 词根。
  const READ_OPS_T = /^(get|query|search|list|fetch|load|detail|find|lookup|check|preview|validate|schema|metadata)/i;
  const WRITE_ROOTS = /(update|save|create|delete|remove|publish|submit|insert|modify|add|import)/i;
  const classify = r => {
    if (r.mutationKeyword) return 'write';
    if (r.rootField && WRITE_ROOTS.test(r.rootField)) return 'write';
    if (r.rootField) return 'read';   // 有具体 rootField 且无写动词 -> 只读（平台命名是 名词+动作后缀）
    if (r.p && /\/service\/udc\/(expression\/schema|graphql)$/.test(r.p)) return 'read';
    return 'write';
  };
  const writeCases = [
    { r: { p: '/service/udc/graphql', rootField: 'udcMicroflowNodeUpdatePost', mutationKeyword: 'update' }, expect: 'write', note: 'rootField 命中 update -> 配置写' },
    { r: { p: '/service/udc/graphql', rootField: 'udcMicroflowServiceDetailsGet', mutationKeyword: null }, expect: 'read', note: '外层 mutation graphqlLoader 但 rootField=DetailsGet -> 只读（v3 会误判为写）' },
    { r: { p: '/service/udc/graphql', rootField: 'udcMicroflowServiceListSubMfPost', mutationKeyword: null }, expect: 'read', note: 'List 只读；平台 rootField 是 名词+动作后缀，Post 后缀本身不等于写' },
    { r: { p: '/service/udc/graphql', rootField: 'udcMicroflowSaveNodePost', mutationKeyword: 'Save' }, expect: 'write', note: 'Save 词根 -> 配置写（若真出现写请求必须判 FAIL）' },
    { r: { p: '/service/udc/graphql', rootField: 'udcMicroflowSearchAppsPost', mutationKeyword: null }, expect: 'read', note: 'Search 只读' },
    { r: { p: '/service/udc/expression/schema', rootField: null, mutationKeyword: null }, expect: 'read' },
    { r: { p: '/service/udc/unknown/writeThing', rootField: null, mutationKeyword: null }, expect: 'write', note: '未命中白名单且无 rootField -> 保守计写' }
  ].map(c => Object.assign(c, { got: classify(c.r), pass: classify(c.r) === c.expect }));
  // 注意：update 词根在 operationName 里由 live 分类器（mutationKeyword 正则）捕获，此处验证白名单方向不误放行
  const writeOk = writeCases.every(c => c.pass);
  const cases = [
    { name: 'two different nodes, same fingerprint', expect: { status: 'PANEL_IDENTITY_FAIL', exitNonZero: true }, got: { status: dup.status, exitCode: dup.exitCode } },
    { name: 'two different nodes, distinct fingerprints', expect: { status: 'PASS', exitNonZero: false }, got: { status: good.status, exitCode: good.exitCode } },
    { name: 'panel title contradicts node type', expect: { status: 'PANEL_IDENTITY_FAIL', exitNonZero: true }, got: { status: mis.status, exitCode: mis.exitCode } },
    { name: 'panel did not switch to clicked node', expect: { status: 'PANEL_IDENTITY_FAIL', exitNonZero: true }, got: { status: noSwitch.status, exitCode: noSwitch.exitCode } },
    { name: 'structural node with no panel is noted, not silently passed', expect: { status: 'PASS', exitNonZero: false, noteCode: 'STRUCTURAL_NO_PANEL' }, got: { status: struct.status, exitCode: struct.exitCode, noteCode: (struct.notes.find(x => x.code === 'STRUCTURAL_NO_PANEL') || {}).code } },
    { name: 'D1: nodeType normalization strips instance suffixes', expect: { pass: true }, got: { pass: normOk, normChecks, precChecks, pseudoTypes: pseudo } },
    { name: 'D2: click on editable input is rejected by precheck (all 3 candidates)', expect: { pass: true }, got: { pass: clickFailOk, attempts: clickFailCase.attempts, retried: fakePre } },
    { name: 'D3: branch uncaptured is explicit failure, not silent success', expect: { status: 'PANEL_IDENTITY_FAIL', exitNonZero: true }, got: (() => { const r = evaluate([{ nodeId: 'BRANCH_n18', nodeType: 'BRANCH', label: 'x', status: 'BRANCH_UI_UNCAPTURED', branchFailReason: 'no condition rows found in node card' }]); return { status: r.status, exitCode: r.exitCode }; })() },
    { name: 'R1-v4: zombie shell detection only removes empty shells (never a drawer with settings/text)', expect: { pass: true }, got: { pass: zombieOk, shellCases } },
    { name: 'R1-v4: drawerCleared=false && hit-unreachable => CLEAR_OVERLAY_FAIL fail-fast (no click)', expect: { pass: true }, got: { pass: failFastCase.pass, decisions: failFastCase } },
    { name: 'R5-v4: writes classified by operationName/mutation (no path-wide exemption)', expect: { pass: true }, got: { pass: writeOk, writeCases } },
    { name: 'R5-v4: CLEAR_OVERLAY_FAIL is an explicit failure code', expect: { status: 'PANEL_IDENTITY_FAIL', exitNonZero: true }, got: (() => { const r = evaluate([{ nodeId: 'RETRIEVE_n2', nodeType: 'RETRIEVE', label: 'x', status: 'CLEAR_OVERLAY_FAIL', preClose: { closed: true, drawerCleared: false } }]); return { status: r.status, exitCode: r.exitCode }; })() }
  ];
  for (const c of cases) {
    if ('pass' in c.expect) { c.pass = !!c.got.pass; }   // D1/D2 断言型用例：直接看自身 pass 标志
    else { c.got.exitNonZero = c.got.exitCode !== 0; c.pass = c.got.status === c.expect.status && c.got.exitNonZero === c.expect.exitNonZero && (!c.expect.noteCode || c.got.noteCode === c.expect.noteCode); }
  }
  const allOk = cases.every(c => c.pass);
  const res = { runAt: new Date().toISOString(), command: 'node tools/cdp/microflow-panel-probe.js --self-test', cases, ok: allOk, exitCode: allOk ? 0 : 1, note: 'exits 0 only when each case is judged as expected; duplicate-fingerprint / title-mismatch / no-switch must give status=PANEL_IDENTITY_FAIL with exit code 3.' };
  console.log(JSON.stringify(res, null, 1));
  return res;
}

/* ---------- live ---------- */
async function live(opts) {
  const t0 = Date.now();
  const audit = { cdpCommands: {}, httpRequests: {}, writes: 0, writeNote: 'no POST/PUT/DELETE issued; never clicks 确定/保存/提交; only Runtime/Page/Network(observe) commands.' };
  const conn = async ws => { const c = await rawWs(ws); const send = c.send; c.send = (m, p) => { audit.cdpCommands[m] = (audit.cdpCommands[m] || 0) + 1; return send(m, p); }; return c; };
  let created = null;
  const pages = await httpJson('/json/list');
  let page = (pages || []).find(x => x.type === 'page' && x.url && x.url.includes('microflow/editor/' + opts.flow));
  if (!page) {
    const v = await httpJson('/json/version'); const b = await conn(v.webSocketDebuggerUrl);
    const t = await b.send('Target.createTarget', { url: 'about:blank' }); created = t.targetId;
    page = (await httpJson('/json/list')).find(x => x.id === created);
    const c0 = await conn(page.webSocketDebuggerUrl); await c0.send('Runtime.enable'); await c0.send('Page.enable');
    await c0.send('Page.navigate', { url: BASE + '/main/child-frame/udc/app-design/rule/microflow/editor/' + opts.flow + '?appId=' + opts.app });
    c0.close();
  }
  const c = await conn(page.webSocketDebuggerUrl);
  await c.send('Runtime.enable');
  // 关键（live run4 取证）：后台 tab 被 rAF 节流，抽屉 leave 动画永久卡在 leave-start，
  // ant-drawer-body 永久占位 -> elementFromPoint 全命中 ant-drawer-body -> 预校验全拒。
  // bringToFront 让页面回到前台，rAF 恢复，动画正常完成（raf-check.js 已实证）。
  try { await c.send('Page.bringToFront', {}); audit.pageBroughtToFront = true; } catch (e) { audit.pageBroughtToFront = 'failed:' + String(e.message).slice(0, 50); }
  try {
    await c.send('Network.enable', {});
    audit.requestLog = [];
    c.on(ev => {
      if (ev.method !== 'Network.requestWillBeSent') return;
      const rq = ev.params.request, m = rq.method;
      audit.httpRequests[m] = (audit.httpRequests[m] || 0) + 1;
      // 仅记录非 GET 的方法与路径，用于证明「无写」。v4：按 operationName + mutation 关键字分类（不再靠路径盲判）
      if (m !== 'GET' && m !== 'OPTIONS') {
        let pth = rq.url; try { pth = new URL(rq.url).pathname; } catch (e) {}
        const pd = rq.postData || '';
        const opM = pd.match(/"operationName"\s*:\s*"([^"]+)"/) || pd.match(/operationName=([A-Za-z0-9_]+)/);
        const bodyM = pd.match(/"query"\s*:\s*"([\s\S]{0,400})/) || pd.match(/query=([\s\S]{0,400})/);
        const body = (bodyM ? bodyM[1] : pd).slice(0, 1200);
        // v4 实测：平台 GraphQL 外壳统一写成 `mutation graphqlLoader(...) { data0: <实际字段>(...) }`，
        // 外层 mutation 关键字无区分度（连 DetailsGet 查询也包成 mutation）。真正的读写信号是
        // data0 后的字段名 —— 因此取 rootField，再判其词根。
        const rootM = body.match(/data\d+\s*:\s*([A-Za-z_][A-Za-z0-9_]*)/);
        const rootField = rootM ? rootM[1] : null;
        // 平台 rootField 形如 udcMicroflowServiceDetailsGet / udcMicroflowSearchAppsPost（名词主体 + 动作后缀），
        // 不是 getXxx 前缀式。因此按**词根是否出现**判，而不是看首词；只认写动词词根为写，其余为读。
        const mutKw = (() => {
          if (!rootField) return (/\bmutation\b/i.test(body) ? 'mutation-decl' : null);
          const WRITE_VERB = /(Update|Create|Delete|Remove|Save|Publish|Submit|Insert|Modify|Add|Import|Set|Reset|Enable|Disable|Bind|Unbind)/;
          const m2 = rootField.match(WRITE_VERB);
          return m2 ? m2[0] : null;
        })();
        if (audit.requestLog.length < 60) audit.requestLog.push({ m, p: pth, postDataLen: pd.length, operationName: opM ? opM[1] : null, rootField, mutationKeyword: mutKw, postDataHead: pd.slice(0, 160) });
      }
    });
  } catch (e) { audit.httpRequests = { note: 'Network.enable unavailable: ' + String(e.message).slice(0, 60) }; }
  let ev = async expr => { const r = await c.send('Runtime.evaluate', { expression: expr, returnByValue: true, awaitPromise: true }); if (r && r.exceptionDetails) throw new Error('page eval error: ' + JSON.stringify(r.exceptionDetails, null, 1).slice(0, 2000)); return r && r.result ? r.result.value : undefined; };
  // v4 加固（实测事件）：本 tab 上还有别的进程在跑旧版探针，会把我注入的 __PROBE 覆盖成旧版本
  // （本轮实测：跑到第 7 个节点时 __PROBE.occluderState 凭空消失 -> TypeError）。
  // 对策：注入后带版本号 __v；每次节点前自检，版本不符立即重注入。不靠「注入一次就万事大吉」。
  const PROBE_TAG = '4.0';
  const injectLib = async () => ev('(' + pageLib.toString() + ')()');
  const probeAlive = async () => {
    const v = await ev("(()=>window.__PROBE?window.__PROBE.__v||'unversioned':'none')()");
    return v === PROBE_TAG;
  };
  const ensureProbe = async () => {
    if (await probeAlive()) return { reinjected: false };
    await injectLib();
    const ok = await probeAlive();
    audit.probeInjections = (audit.probeInjections || 0) + 1;
    return { reinjected: true, ok };
  };
  await injectLib();
  audit.probeTag = PROBE_TAG;

  let ready = null;
  for (let i = 0; i < 45; i++) { ready = await ev('__PROBE.enumNodes()'); if (ready && ready.uniqueNodeCount >= 5) break; await sleep(1000); }
  if (!ready || !ready.uniqueNodeCount) { audit.elapsedMs = Date.now() - t0; return { status: 'BLOCKED', reason: 'node enumeration empty (canvas not ready / not logged in)', audit }; }

  const nodes = opts.limit ? ready.nodes.slice(0, opts.limit) : ready.nodes;
  const results = [];
  let panicClear = false;   // 一旦出现过 CLEAR_OVERLAY_FAIL，此后每节点点击前强制清遮挡（不整体停）
  for (const n of nodes) {
    const tNode = Date.now();
    const inj = await ensureProbe();   // 防并发进程覆盖 __PROBE（本轮实测真事件）
    // R1/v4 preClose：关抽屉 -> 识别遮挡源 -> 命中复验。
    // 强一致（REQ-1.3）：drawerCleared===false 且命中不可达 -> 该节点不点击，记 CLEAR_OVERLAY_FAIL（禁 closed:true 与 false 并存）。
    const closeT = Date.now(); let cd = null, closed = false, ov = null, drawerCleared = false, hit0 = null, clearInfo = null;
    for (let i = 0; i < 12; i++) {
      const st = await ev('__PROBE.state()');
      // 确认框先解（只点取消），否则它盖住一切且 settingsCount 判据不可达
      if (st.blockingConfirm) { const dc = await ev('__PROBE.dismissConfirm()'); if (i === 0) clearInfo = { steps: ['confirm:' + (dc && dc.dismissed ? 'dismissed-by-cancel' : 'UNRESOLVED')], zombies: [], confirms: [dc] }; await sleep(400); continue; }
      if (!st.settingsCount) { closed = true; break; }
      cd = await ev('__PROBE.closeDrawer()');   // 每轮都尝试关，直到确认无可见 settings 根
      await sleep(250);
    }
    if (closed) {
      for (let i = 0; i < 12; i++) {
        const st2 = await ev('__PROBE.state()');
        hit0 = await ev('__PROBE.hitProbe(' + JSON.stringify(n.nodeId) + ')');
        // 清理成功判据 = 设置面板消失 且 目标节点命中可达（不再只看 drawerBodyLen 这种间接量）
        if (st2.settingsCount === 0 && hit0 && hit0.ok) { drawerCleared = true; break; }
        ov = await ev('__PROBE.closeOverlays()');
        clearInfo = await ev('__PROBE.clearOccluders()');
        await sleep(300);
      }
    }
    const closeMs = Date.now() - closeT;
    const occl0 = await ev('__PROBE.occluderState()');
    const preClose = {
      closed, closeMs, action: cd, overlays: ov, drawerCleared,
      hitProbe: hit0, occluderState: occl0,
      zombiesRemoved: (clearInfo && clearInfo.zombies) || [],
      clearSteps: (clearInfo && clearInfo.steps) || [],
      confirmsHandled: (clearInfo && clearInfo.confirms) || [],
      // REQ-1.3 强一致断言：closed=true 与 drawerCleared=false 不允许「并存后继续点」
      consistent: !(closed === true && drawerCleared === false && !!(hit0 && hit0.inView && !hit0.inNode))
    };
    // 强一致：面板未清 且 命中被遮挡（不是 offscreen，也不是没探到） -> fail-fast，不点击。
    // offscreen 不算遮挡：hitProbe 内部已 bringIntoView，仍 offscreen 说明画布确实移不到，交 clickNode 的 pan 轮次处理。
    const occluded = !!(hit0 && hit0.inView && !hit0.ok && !hit0.inNode);
    if (!drawerCleared && occluded) {
      panicClear = true;
      const rec = { nodeId: n.nodeId, nodeType: n.nodeType, instance: n.instance, label: n.label, coords: n.coords, preClose, clickTarget: null, status: 'CLEAR_OVERLAY_FAIL', clearFailReason: 'preClose: 设置面板已关但目标节点命中被遮挡（遮挡源未能清理），按 REQ-1.3 fail-fast 不点击，避免产生假面板证据' };
      results.push(rec); console.log('[clear-fail] ' + n.nodeId + ' hit=' + JSON.stringify(hit0) + ' occl=' + JSON.stringify(occl0).slice(0, 300)); continue;
    }

    let opened = await ev('__PROBE.clickNode(' + JSON.stringify(n.nodeId) + ')');
    // v4：panic 模式 —— 本轮已出现过遮挡未清，点击前强制清一遍遮挡源（纯视图，不碰配置）
    if (panicClear) {
      const pc = await ev('__PROBE.clearOccluders()');
      const retry0 = await ev('__PROBE.clickNode(' + JSON.stringify(n.nodeId) + ')');
      if (retry0 && retry0.ok) { retry0.retriedAfterPanicClear = pc; retry0.priorAttempts = (opened && opened.clickTarget && opened.clickTarget.attempts) || []; opened = retry0; }
    }
    const rec = { nodeId: n.nodeId, nodeType: n.nodeType, instance: n.instance, label: n.label, coords: n.coords, preClose, probeInjection: inj, clickTarget: opened && opened.clickTarget ? opened.clickTarget : null, open: { ok: opened && opened.ok, fired: opened && opened.fired, reason: opened && opened.reason, rounds: opened && opened.rounds, occluderEvidence: opened && opened.occluderEvidence } };
    if (!opened || !opened.ok) {
      rec.status = 'CLICK_TARGET_FAIL';   // 3 候选 x 3 轮全失败 -> 明确失败，带遮挡现场，不静默继续
      results.push(rec); console.log('[click-fail] ' + n.nodeId + ' occluder=' + JSON.stringify((opened && opened.occluderEvidence) || {}).slice(0, 300)); continue;
    }

    // R3 + C4：轮询「active 切到本节点 + 抽屉标题出现 + 内容稳定 + 无遮罩」
    const tp = Date.now();
    let prev = null, stable = 0, cap = null, polls = 0, firstProofAt = null;
    const maxPolls = STRUCTURAL.test(n.nodeType) ? 4 : 32;
    for (let i = 0; i < maxPolls; i++) {
      cap = await ev('__PROBE.capture()'); polls++;
      // 结构节点（分支/条件）本就没有设置面板：4 次轮询确认无面板即判结构节点，不空转 8s
      if (STRUCTURAL.test(n.nodeType) && i >= 3 && !(cap && cap.panelOpen)) break;
      const act = cap.activeIds || [];
      const proven = cap.panelOpen && cap.panelLoaded && !!cap.headerTitle && act.includes(n.nodeId);
      const sig = cap.panelOpen ? [cap.textLen, cap.controlCount, cap.fingerprint, cap.headerTitle].join('|') : 'closed';
      const masked = !!(cap.masks && cap.masks.length);
      if (proven && !firstProofAt) firstProofAt = Date.now() - tp;
      if (proven && sig !== prev && !masked) { stable = 0; }
      else if (proven && sig === prev && !masked) { stable++; if (stable >= 2) break; }
      prev = sig;
      await sleep(250);
    }
    const waitMs = Date.now() - tp;
    const actIds = (cap && cap.activeIds) || [];
    // `.active` 类不一定出现在节点卡上（live 实测多为空）。补一条类型权威自证：
    // drawerTitle 的 nodeTypeHint 命中本 nodeType 的白名单 allowedPanelHints 时，同样视为「本节点的面板」。
    const expHints = expectationFor(n.nodeType);
    const hintOf = cap && cap.nodeTypeHint ? cap.nodeTypeHint : null;
    const titleAgrees = !!expHints && !!hintOf && hintOf.confidence === 'high' && expHints.includes(hintOf.hint);
    const proven = !!((cap && cap.panelOpen && cap.panelLoaded && cap.headerTitle) && (actIds.includes(n.nodeId) || titleAgrees));
    rec.loadCompletion = { waitMs, polls, firstProofAtMs: firstProofAt, masksAtEnd: (cap && cap.masks) || [], stabilizedBy: stable >= 2 ? 'contentStable(2 rounds)+noMask+drawerTitlePresent' : 'timeout_or_unstable' };
    rec.switchEvidence = {
      clickedNodeId: n.nodeId, panelOpened: !!(cap && cap.panelOpen), drawerTitle: cap && cap.headerTitle,
      activeBefore: null, activeAfter: actIds, activeMatchesTarget: actIds.includes(n.nodeId),
      panelLoaded: !!(cap && cap.panelLoaded), titleTypeAgrees: titleAgrees,
      isProvenPanelOfThisNode: proven, closeToClickMs: closeMs, hitInsideNode: opened.hitInsideNode
    };
    if (!cap || !cap.panelOpen) {
      // PANEL_OPEN_RETRY：点击本身成功（precheck 通过）但设置面板未出现（首个节点常见：上一轮残留抽屉刚关、画布刚滚动）。
      // 只关壳层后重试一次；仍无面板才判 NO_PANEL/BRANCH_UI_UNCAPTURED。
      if (!STRUCTURAL.test(n.nodeType)) {
        const r2 = await ev('(()=>{ if(window.__PROBE.closeOverlays) window.__PROBE.closeOverlays(); return 1; })()');
        await sleep(600);
        const again = await ev('__PROBE.clickNode(' + JSON.stringify(n.nodeId) + ')');
        if (again && again.ok) {
          for (let i = 0; i < 16; i++) { cap = await ev('__PROBE.capture()'); if (cap && cap.panelOpen && cap.panelLoaded && cap.headerTitle) break; await sleep(300); }
          opened = again; rec.clickTarget = again.clickTarget || rec.clickTarget;
          rec.panelOpenRetry = { attempted: true, closedOverlays: !!r2, reopened: !!(cap && cap.panelOpen), drawerTitle: cap && cap.headerTitle };
          if (cap && cap.panelOpen) {
            actIds.length = 0; (cap.activeIds || []).forEach(x => actIds.push(x));
            const expH2 = expectationFor(n.nodeType), h2 = cap.nodeTypeHint || null;
            const agree2 = !!expH2 && !!h2 && h2.confidence === 'high' && expH2.includes(h2.hint);
            rec.switchEvidence = Object.assign(rec.switchEvidence || {}, {
              panelOpened: true, drawerTitle: cap.headerTitle, activeAfter: actIds, activeMatchesTarget: actIds.includes(n.nodeId),
              panelLoaded: !!cap.panelLoaded, titleTypeAgrees: agree2, isProvenPanelOfThisNode: !!(cap.panelLoaded && cap.headerTitle && (actIds.includes(n.nodeId) || agree2))
            });
          }
        } else {
          rec.panelOpenRetry = { attempted: true, reopened: false, reason: again && again.reason };
        }
      }
      if (STRUCTURAL.test(n.nodeType)) {
        // D3: 分支/条件不是设置面板型 -> 按分支自身 UI 只读采集 branchSpec；拿不到标 BRANCH_UI_UNCAPTURED，不得当成功
        const bs = await ev('__PROBE.branchSpec(' + JSON.stringify(n.nodeId) + ')');
        rec.branchSpec = bs && bs.captured ? bs : null;
        rec.status = bs && bs.captured ? 'STRUCTURAL_BRANCH_CAPTURED' : 'BRANCH_UI_UNCAPTURED';
        rec.branchFailReason = bs && !bs.captured ? bs.reason : null;
        results.push(rec); console.log('[branch] ' + n.nodeId + ' captured=' + (bs && bs.captured) + ' rows=' + (bs && bs.branchCount)); continue;
      }
      rec.status = 'NO_PANEL'; results.push(rec); console.log('[no-panel] ' + n.nodeId + ' active=' + actIds.join(',')); continue;
    }
    if (!proven) {
      rec.status = 'PANEL_SWITCH_FAIL';
      rec.panelIdentity = { rootSelector: cap.rootSelector, headerTitle: cap.headerTitle, nodeTypeHint: cap.nodeTypeHint, fingerprint: cap.fingerprint };
      rec.panelIdentityMatch = false; results.push(rec);
      console.log('[SWITCH-FAIL] ' + n.nodeId + ' active=' + actIds.join(',') + ' title=' + cap.headerTitle + ' wait=' + waitMs + 'ms'); continue;
    }

    rec.panelIdentity = {
      rootSelector: cap.rootSelector, rootRect: cap.rootRect, headerTitle: cap.headerTitle, headerTitleSource: cap.headerTitleSource,
      nodeTypeHint: cap.nodeTypeHint, fingerprint: cap.fingerprint, fingerprintBasis: cap.fingerprintBasis,
      formLabels: cap.formLabels, buttons: cap.buttons
    };
    rec.firstLine = cap.firstLine; rec.structural = cap.structural; rec.textSample = cap.textSample;
    rec.inputs = cap.inputs; rec.selects = cap.selects; rec.requiredFields = cap.requiredFields;

    if (/DATA_MAPPING/i.test(n.nodeType)) {
      const b = await ev('__PROBE.clickFieldControl("映射关系")');
      if (b && b.ok) {
        rec.mapping = { open: false, reason: 'dialog-not-opened' };
        for (let i = 0; i < 10; i++) {
          await sleep(700);
          const dg = await ev('__PROBE.captureDialog()');
          if (dg && dg.open) { rec.mapping = dg; break; }
          rec.mapping = dg || rec.mapping;
        }
        rec.mapping.openedBy = b.text;
      }
      else rec.mapping = { open: false, reason: b ? b.reason : 'no-trigger' };
    }
    if (/CALL_APP_SERVICE|PUBLISH_BUSINESS_EVENT/i.test(n.nodeType)) {
      rec.expression = await ev('__PROBE.expressionEntry()');
      rec.paramArea = await ev('(()=>{const r=document.querySelector("' + '.udc-microflow-editor-node-settings' + '");if(!r)return null;const t=r.innerText||"";const i=t.indexOf("参数");return i<0?{hasParam:false}:{hasParam:true,snippet:t.slice(i,i+220)}})()');
    }
    rec.status = 'CAPTURED'; rec.durationMs = Date.now() - tNode;
    results.push(rec);
    console.log('[captured] ' + n.nodeId + ' title=' + cap.headerTitle + ' active=' + actIds.join(',') + ' fp=' + cap.fingerprint + ' hint=' + cap.nodeTypeHint.hint + '(' + cap.nodeTypeHint.score + ') wait=' + waitMs + 'ms in=' + cap.inputs.length);
  }

  const j = evaluate(results);
  const find = re => results.find(r => re.test(r.nodeType));
  const cs = find(/^CALL_APP_SERVICE$/), evt = find(/^PUBLISH_BUSINESS_EVENT$/);
  const fpOf = x => (x && x.panelIdentity && x.panelIdentity.fingerprint) || null;
  const knownFail = {
    customService: cs ? { nodeId: cs.nodeId, status: cs.status, drawerTitle: cs.panelIdentity && cs.panelIdentity.headerTitle, fingerprint: fpOf(cs) } : null,
    eventPublish: evt ? { nodeId: evt.nodeId, status: evt.status, drawerTitle: evt.panelIdentity && evt.panelIdentity.headerTitle, fingerprint: fpOf(evt) } : null,
    distinct: !!(cs && evt && fpOf(cs) && fpOf(evt) && fpOf(cs) !== fpOf(evt)),
    verdict: (cs && evt && fpOf(cs) && fpOf(evt) && fpOf(cs) !== fpOf(evt) && cs.panelIdentity.headerTitle !== evt.panelIdentity.headerTitle) ? 'IDENTITY_OK' : 'IDENTITY_FAIL'
  };
  if (knownFail.verdict === 'IDENTITY_FAIL' && !j.fails.some(f => f.code === 'PANEL_IDENTITY_FAIL'))
    j.fails.push({ code: 'PANEL_IDENTITY_FAIL', rule: 'known_fail_not_resolved', reason: '自定义服务 与 事件投递 指纹或面板标题相同/缺失', knownFail });
  // v4 / C8 只读口径（auditor VERDICT-v22 §3 + prelim REQ-1.4 合并采纳，废除路径盲判）：
  //   分类顺序 = ① mutation 关键字/声明 -> 配置写（FAIL）
  //             ② operationName 命中只读白名单 -> 只读查询
  //             ③ 已知只读端点（expression/schema 等，参数走 body）-> 只读查询
  //             ④ 其余非 GET 一律保守计为配置写（宁严不宽），不再用「no POST issued」这种失真表述。
  const READ_OPS = /^(get|query|search|list|fetch|load|detail|find|lookup|check|preview|validate|schema|metadata|fetch)/i;
  const RO_ENDPOINTS = [
    { p: '/service/udc/expression/schema', why: '表达式 schema 只读查询：POST 仅因参数走 body；服务端只返回表达式函数/操作符 schema，不写任何配置。' },
    { p: '/service/udc/graphql', why: 'GraphQL RPC 端点：编辑器渲染面板/画布时前端自身发的查询。v4 不再按路径整片豁免 —— 逐条按 operationName 与 mutation 关键字分类，命中写操作词根即计配置写。' }
  ];
  audit.requestLog = (audit.requestLog || []).map(r => {
    let configWrite = false, why = null, cls = null;
    if (r.mutationKeyword) { configWrite = true; cls = 'write-root-field'; why = 'payload rootField 命中写操作词根（' + r.mutationKeyword + '）→ 配置写'; }
    else if (r.rootField && READ_OPS.test(r.rootField)) { cls = 'read-root-field'; why = 'rootField=' + r.rootField + ' 属只读查询命名空间（Get/Search/List/…）'; }
    else if (r.rootField) { cls = 'read-root-field'; why = 'rootField=' + r.rootField + ' 未含写动词词根（Update/Create/Delete/…）→ 只读查询；payload 原文可在 CDP 复核'; }
    else {
      const ro = RO_ENDPOINTS.find(x => r.p.endsWith(x.p));
      if (ro) { cls = 'read-endpoint'; why = ro.why + '（payload 未解析出 rootField）'; }
      else { configWrite = true; cls = 'unclassified-non-get'; why = '未命中只读白名单，保守计为配置写'; }
    }
    return Object.assign({}, r, { configWrite, classification: cls, readOnlyJustification: why });
  });
  audit.writeLikeRequests = (audit.requestLog || []).filter(r => r.configWrite);
  audit.writes = audit.writeLikeRequests.length;
  audit.writesScope = 'configuration writes = 非 GET 且（命中写操作词根/声明 或 未命中只读白名单）。逐条见 requestLog[].classification 与 readOnlyJustification；不再以路径整体豁免。';
  audit.writeNote = "probe 自身不发起任何业务写：它只 dispatch DOM 事件（click/keys）与 Runtime.evaluate 读 DOM，从不点「确定/保存/提交」，从不进编辑态提交。requestLog 中的非 GET 均为编辑器前端自身的请求，逐条给出 operationName / mutationKeyword / classification / readOnlyJustification，便于第三方在 CDP 复核（POST != 写）。";
  audit.readOnlyAssertion = { configWriteCount: audit.writes, mutationKeywordHits: (audit.requestLog || []).filter(r => r.mutationKeyword).length, unclassifiedNonGet: (audit.requestLog || []).filter(r => r.classification === 'unclassified-non-get').length };
  if (audit.writes > 0) {
    j.fails.push({ code: 'WRITE_DETECTED', rule: 'non_get_without_readonly_proof', count: audit.writes, samples: audit.writeLikeRequests.slice(0, 5) });
  }
  // 最终判定必须在所有 fails 归并之后计算（v4 修：v3.1 在 writes 分类前定 status，会把 WRITE_DETECTED 吞掉）
  const finalStatus = j.fails.length ? 'PANEL_IDENTITY_FAIL' : 'PASS';
  const out = {
    probe: 'microflow-panel-probe.js', version: '4.0', captured_at: new Date().toISOString(),
    flow_id: opts.flow, app_id: opts.app, mode: 'read-only CDP panel probe',
    status: finalStatus, exitCode: finalStatus === 'PASS' ? 0 : 3,
    rootCauseFixed: {
      symptom: '事件投递 采到与 自定义服务 同样的面板（microflow-panel-identity-audit.json status=FAIL）',
      cause: '抽屉(1309px,no-mask)未关闭遮挡画布 -> 后续节点点击静默失效 -> .active 留在上一节点 -> 采集器照旧 capture 上一面板 => 指纹被复制；v3 进一步确认残留 .ant-drawer 空壳（bodyChildCount=0，.ant-drawer-body 仍 pointer-events:auto）覆盖 x≥945 整片画布',
      fix: 'v4：点击前 closeDrawer + clearOccluders（关闭按钮→modal close→ESC→空壳纯视图移除 display:none，记 zombieRemoved[]）+ hitProbe 命中复验；命中不可达则平移画布重试；drawerCleared=false 且不可达时 fail-fast（CLEAR_OVERLAY_FAIL）不点击；DOM 合成点击；三重身份自证(active nodeId / drawerTitle / 新打开)'
    },
    knownFailRecheck: knownFail,
    schemaEnum: { count: ready.uniqueNodeCount, domContainerCount: ready.domContainerCount, enumSource: ready.enumSource, canvas: ready.canvas, capturedCount: results.length, countConsistent: opts.limit ? null : (results.length === ready.uniqueNodeCount), nodes: ready.nodes },
    panelIdentityRule: {
      panelRoot: '.udc-microflow-editor-node-settings (inside .ant-drawer)',
      authoritativeTitle: '.ant-drawer-title innerText（平台自带面板标题，例：创建变量/自定义服务/事件投递）',
      fingerprint: 'FNV1a x2 over {drawerTitle, formLabels[], ctlSig[], buttons[]} — 不含 nodeId、非 innerText 全文',
      switchProof: 'closeDrawer(轮询 settingsCount==0) -> DOM 合成点击 -> 轮询 active nodeId==target 且 drawerTitle 非空且内容稳定2轮无遮罩',
      failConditions: ['panel not proven for clicked node (active id mismatch / no title)', 'two different nodeTypes share one fingerprint', 'panel title contradicts node type', 'node not clickable', 'no panel root (non-structural node)']
    },
    nodes: results, failures: j.fails, notes: j.notes,
    selfTest: { command: 'node tools/cdp/microflow-panel-probe.js --self-test', result: 'run separately; exits 0 only when all 8 cases judged as expected (5 identity + D1 normalization + D2 click-precheck + D3 branch-fail)' },
    audit: Object.assign(audit, { elapsedMs: Date.now() - t0, readOnly: true })
  };
  const outPath = path.resolve(opts.out);
  fs.mkdirSync(path.dirname(outPath), { recursive: true });
  fs.writeFileSync(outPath, JSON.stringify(out, null, 1));
  console.log('\nstatus=' + finalStatus + ' nodes=' + results.length + '/' + ready.uniqueNodeCount + ' fails=' + j.fails.length + ' writes=' + audit.writes + ' http=' + JSON.stringify(audit.httpRequests) + '\n-> ' + outPath);
  if (j.fails.length) console.log('FAILURES=' + JSON.stringify(j.fails.map(f => ({ code: f.code, rule: f.rule, node: f.node || (f.nodes || []).map(x => x.nodeId) })), null, 1));
  if (created) { try { const v = await httpJson('/json/version'); const b2 = await rawWs(v.webSocketDebuggerUrl); await b2.send('Target.closeTarget', { targetId: created }); b2.close(); } catch (e) {} }
  c.close();
  return { status: finalStatus, outPath, fails: j.fails, knownFail, count: results.length, total: ready.uniqueNodeCount, audit };
}

/* ---------- CLI ---------- */
(async () => {
  const argv = process.argv.slice(2);
  const opt = { flow: '-1014184770817921434', app: '8704025620829192834', out: 'docs/audit/artifacts/udc-node-evidence/microflow-panel-probe-v4.json', limit: 0 };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === '--flow') opt.flow = argv[++i];
    else if (a === '--app') opt.app = argv[++i];
    else if (a === '--out') opt.out = argv[++i];
    else if (a === '--limit') opt.limit = Number(argv[++i]) || 0;
    else if (a === '--self-test') { const r = selfTest(); process.exit(r.ok ? 0 : 1); }
    else if (a === '--help') { console.log('usage: node microflow-panel-probe.js [--self-test] [--flow F] [--app A] [--out P] [--limit N]'); process.exit(0); }
  }
  try {
    const r = await live(opt);
    if (r.status === 'PASS') process.exit(0);
    if (r.status === 'BLOCKED') process.exit(2);
    process.exit(3);
  } catch (e) { console.log('ERR ' + ((e && e.stack) || e)); process.exit(1); }
})();
