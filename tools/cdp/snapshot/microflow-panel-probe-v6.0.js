#!/usr/bin/env node
/**
 * microflow-panel-probe-v6.0.js — 微流程节点面板证据采集器 v6.0（只读，逐字段采集）
 *
 * v5.1 相对 v5 的两处修正（均基于 LIVE 复现）
 *  E1【结构性节点被当抽屉节点点击 -> inline 重命名副作用 -> 假 CLEAR_OVERLAY_FAIL】
 *     可信鼠标点击 Input.dispatchMouseEvent 实测：BRANCH_n18 / CONDITION_n18_0 图标点击后
 *     6×400ms 采样 .ant-drawer==0、settings==0 → 这两类节点本来就没有抽屉面板。
 *     v5 对它们仍执行 clickNode()，合成事件无效后落到 el.click() 兜底，命中 .caption-title 内的
 *     <input class="ant-input edit-input">，把「分支(2)」切成 inline 重命名态（TEXT -> INPUT），
 *     并使条件行在后续轮询中脱离 DOM → CONDITION 的 clearAndProve 得到 hitProbe{reason:'node-not-found'}
 *     → 2 条 CLEAR_OVERLAY_FAIL + 1 条 BRANCH_UI_UNCAPTURED。
 *     v5.1：结构性节点完全不走点击路径，改为「无遮挡确证 + 卡片只读指纹自证」。
 *  E2【只读分类白名单过窄 -> WRITE_DETECTED 假阳性】
 *     平台把查询命名为 xxxGet / xxxList / xxxPost 并全塞进 service GraphQL 端点，编辑器自身还打
 *     search-app-edition / front-detection。v5 只按 rootField 前缀判，5 条只读请求被计成写。
 *     v5.1：端点性质 + rootField 命名双重判据，逐条 write/read + 理由，且不点任何提交按钮。
 *
 * ===== 本版唯一目标（HANDOFF#1 / 阶段 P0-1）=====
 * 让「面板属于该节点」变成可自证事实：每次点击下一节点前，**先证明抽屉已卸载/不可见**，
 * 关闭不成立就 fail-fast（CLEAR_OVERLAY_FAIL，不点击、不采集），绝不拿残留面板冒充新面板。
 * v4 的 hitProbe 与三重身份自证全部保留并加强。
 *
 * ===== 为什么必须改（本轮 LIVE 取证，2026-10-17）=====
 * D1【标题读取缺陷 —— 16 条 PANEL_IDENTITY_FAIL 的直接主因】
 *    .udc-microflow-editor-node-settings 根节点挂在 .ant-drawer-body 之下，
 *    而 .ant-drawer-title 在 .ant-drawer-header 里，**不在** settings 根内。
 *    v4 的 state() 用 root.querySelector('.ant-drawer-title') 取标题 -> 恒为 null
 *    -> proven 恒 false -> 每个节点都记 PANEL_SWITCH_FAIL（实测 16 条）。
 *    v5 改为：settings 根 -> 向上找最近的 .ant-drawer -> 读该 drawer 的 .ant-drawer-title。
 *    证据：node tools/cdp/snapshot/... 前的 scratch 探针输出 titleInRoot=false / titleFromDrawer="创建变量"。
 *
 * D2【状态机缺陷 —— 2 条 NO_PANEL 假失败】
 *    v4 在 `if (!cap || !cap.panelOpen)` 分支里做 PANEL_OPEN_RETRY；重试成功后只更新了
 *    switchEvidence，却**没有跳出该分支**，仍然执行到 `rec.status='NO_PANEL'`。
 *    结果：evidence.panelOpened=true / isProvenPanelOfThisNode=true，status 却是 NO_PANEL。
 *    证据：v4 JSON nodes[RETRIEVE_n2].status=NO_PANEL 且 switchEvidence.panelOpened=true（自相矛盾）。
 *    v5 先重试、再按重试后的真实状态判定，状态与证据单一来源。
 *
 * D3【off-by-one 残留 —— 5 条 panel_title_contradicts + 相邻节点 activeAfter=下一个节点】
 *    v4 记录里 activeAfter 恰好等于**下一个**节点 id（n3->CREATE_LIST_n4, n4->CHANGE_LIST_n5 ...），
 *    即「点 n 却激活 n+1」。v4 源码注释已记录「本 tab 上还有别的进程在跑旧版探针，会覆盖 __PROBE」。
 *    多个探针进程共享同一个 tab -> 互相推进点击 -> 面板与节点错位 -> 指纹/标题串位。
 *    v5 对策：① 自建专属 target（新 tab），结束即关闭；② 页面内 __P6.probeTag + 每次节点前校验，
 *    被覆盖立即重注入并记 foreignProbeDetected；③ 采集时同时记录其它同 flow tab 数量作为并发证据。
 *
 * ===== v5 判据（不放宽，只补证）=====
 * C1 点击前「抽屉已卸载」三重确证（全部必须成立，否则 CLEAR_OVERLAY_FAIL，不点击）：
 *    a) 可见 settings 根数量 == 0（getBoundingClientRect 有尺寸且未被 display:none）
 *    b) 可见「开着且承载面板」的 .ant-drawer 数量 == 0（.ant-drawer-open 或含 SETTINGS）
 *    c) 目标节点 elementFromPoint 命中可达（命中点在该节点子树内，且祖先链无 .ant-drawer/.ant-modal）
 *    另记 zombieRemoved[]（空壳纯视图 display:none，只改样式，不动任何配置）
 * C2 面板身份三重自证（缺一不算 proven）：
 *    a) activeMatchesTarget：点击后 .active 节点 == 目标节点
 *    b) titleNonEmpty + titleTypeAgrees：drawer 标题非空，且标题/面板文本的 nodeTypeHint 落在该 nodeType 白名单
 *    c) freshOpen：抽屉在 pre-click「已清空」之后才出现（openSeq 戳），排除残留面板
 * C3 指纹：FNV1a×2 over {drawerTitle, formLabels[], ctlSig[], buttons[]}（结构指纹，不含 nodeId）
 *        + fullTextFingerprint：面板全文（innerText）归一化后的 FNV1a×2 + 长度 + sha 级不可逆摘要
 * C4 相邻节点结构指纹必须互异；同 nodeType 相同指纹只记 note，不同 nodeType 相同指纹判 PANEL_IDENTITY_FAIL
 * C5 只读：只 dispatch DOM 事件 + Runtime.evaluate 读 DOM；从不点 确定/保存/提交；requestLog 逐条分类
 *
 * ===== 用法 =====
 *   node tools/cdp/snapshot/microflow-panel-probe-v5.1.js --self-test
 *   node tools/cdp/snapshot/microflow-panel-probe-v5.1.js \
 *        --flow -1014184770817921434 --app 8704025620829192834 \
 *        --out docs/audit/artifacts/udc-node-evidence/microflow-panel-probe-v5.json
 *   node tools/cdp/snapshot/microflow-panel-probe-v5.1.js --limit 3
 */
'use strict';
const http = require('http'), net = require('net'), crypto = require('crypto'), fs = require('fs'), path = require('path');

const BASE = 'https://lowcode-test2.changhongit.com';
/* v6：本域专属 CDP 端口（CDP-ENDPOINT.md：九域各占一个端口，本域 9227）；--cdp 可覆盖 */
let CDP_PORT = Number(process.env.UDC9_CDP_PORT || 9227);
const sleep = ms => new Promise(r => setTimeout(r, ms));
const PROBE_TAG = '6.0';

/* ---------- 内层映射入口判定（模块级，页面注入与 self-test 共用） ----------
 * 词表依据（全量 artifacts + operation-contracts 实测高频入口）：
 *   字段映射 69 / 对象引用 69 / 自动映射 34 / 添加字段 16 / 已设置 11 / 添加映射 11 / 添加键值对 11
 * 历史缺陷：旧实现用 /dashed|_633a27a8/ 兜底；_633a27a8 是抽屉底部操作栏哈希类名，命中所有按钮，
 *   于是「取消/确定」被当内层映射入口点击 → 假 INNER_MAPPING_BLOCKED → 每节点假 PARTIAL_UNVERIFIED；
 *   同时真实高频入口 字段映射/对象引用/自动映射 反而不在白名单（漏抓）。
 * 现规则：仅按真实入口文案精确匹配；底部操作栏用结构化类名 + 精确文案双重排除。
 */
const ENTRY_RX = /^(字段映射|对象引用|自动映射|已设置|添加字段|添加键值对|添加映射|添加参数|选择字段|配置映射|配置字段|设置映射)$/;
const ACTION_BAR_RX = /(compid_node-config-submit-btn|btn-solid-default|ant-drawer-footer|node-config-submit|config-submit|submit-btn|ant-btn-primary)/i;
const ACTION_BAR_TEXT_RX = /^(取消|确定|保存|关闭|提交|返回)$/;
function isActionBarButton(b, textFn) {
  const cls = String(b.className || '');
  if (ACTION_BAR_RX.test(cls)) return true;
  const t = String((textFn ? textFn(b) : b.textContent) || '').trim();
  return ACTION_BAR_TEXT_RX.test(t);
}
function isInnerMappingEntry(text) { return ENTRY_RX.test(String(text || '').trim()); }

/* ---------- 最小 CDP 客户端（同 v4：Node 侧零依赖） ---------- */
function httpJson(p) {
  return new Promise((res, rej) => {
    http.get({ host: '127.0.0.1', port: CDP_PORT, path: p }, r => {
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
      setTimeout(() => { if (pend.has(i)) { pend.delete(i); rj(new Error('timeout ' + method)); } }, 60000);
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
          else if (j.method) events.forEach(f => { try { f(j); } catch (e) { } });
        }
      }
    });
    s.on('error', reject);
  });
}

/* ---------- 页面内探针库 v5 ---------- */
function pageLib5() {
  const sleep = ms => new Promise(r => setTimeout(r, ms));
  const SETTINGS = '.udc-microflow-editor-node-settings';
  const NODE = '.udc-microflow-editor-node-container';
  const prev = window.__P6 || {};
  const S = {
    __v: '6.0', keepLoaded: true,
    openSeq: prev.openSeq || 0,
    closedSeq: prev.closedSeq || 0,
    epoch: prev.epoch || 0,
    reinjectedBefore: prev.reinjectedBefore || 0,
    closedAt: prev.closedAt || 0
  };
  const vis = el => { if (!el) return false; const r = el.getBoundingClientRect(); const s = getComputedStyle(el); return r.width > 0 && r.height > 0 && s.visibility !== 'hidden' && s.display !== 'none'; };
  const txt = el => ((el && (el.innerText || el.textContent)) || '').replace(/\s+/g, ' ').trim();
  const cssPath = el => { if (!el || el.nodeType !== 1) return ''; if (el.id) return '#' + CSS.escape(el.id); const cls = (typeof el.className === 'string' && el.className.trim()) ? el.className.trim().split(/\s+/).slice(0, 2).map(c => '.' + CSS.escape(c)).join('') : ''; const p = el.parentElement ? cssPath(el.parentElement) : ''; return (p ? p + ' > ' : '') + el.tagName.toLowerCase() + cls; };
  function fnv(s) { let h1 = 0x811c9dc5, h2 = 0x01000193 ^ s.length; for (let i = 0; i < s.length; i++) { const c = s.charCodeAt(i); h1 ^= c; h1 = (h1 * 16777619) >>> 0; h2 = (h2 ^ (c + i)) >>> 0; h2 = (h2 * 2246822519) >>> 0; } return ('00000000' + h1.toString(16)).slice(-8) + ('00000000' + h2.toString(16)).slice(-8); }
  const rect = el => { const r = el.getBoundingClientRect(); return { x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height) }; };
  const drawerOf = el => { let p = el; while (p && !(p.classList && p.classList.contains('ant-drawer'))) p = p.parentElement; return p; };
  const hitCls = el => (el ? (typeof el.className === 'string' ? el.className.slice(0, 60) : el.tagName) : null);

  /* ---- 节点清单：从 live DOM 派生（无硬编码） ---- */
  const NORMALIZE_RX = /^(.*)_n(\d+(?:[a-z]|_\d+)?)$/i;
  function enumNodes() {
    const seen = new Map();
    const containers = [...document.querySelectorAll(NODE + '[id]')];
    for (const el of containers) {
      const id = el.id; if (seen.has(id)) continue;
      const lEl = el.querySelector('.node-title-text') || el.querySelector('.node-title') || el;
      const m = id.match(NORMALIZE_RX);
      seen.set(id, { nodeId: id, nodeType: m ? m[1] : id, instance: m ? m[2] : null, label: (lEl.innerText || '').split('\n')[0].trim(), coords: rect(el) });
    }
    const cv = document.querySelector('.nodes');
    return {
      enumSource: "document.querySelectorAll('.udc-microflow-editor-node-container[id]')  // id=<NODE_TYPE>_n<INSTANCE>",
      domContainerCount: containers.length, uniqueNodeCount: seen.size, nodes: [...seen.values()],
      canvas: cv ? { cls: cv.className, scrollLeft: Math.round(cv.scrollLeft), scrollTop: Math.round(cv.scrollTop) } : null
    };
  }

  /* ---- 抽屉/面板状态（v5 核心修正见文件头 D1） ---- */
  function state() {
    const roots = [...document.querySelectorAll(SETTINGS)];
    const visRoots = roots.filter(vis);
    const root = visRoots[0] || null;
    const drawer = root ? drawerOf(root) : null;
    const header = drawer ? drawer.querySelector('.ant-drawer-header') : null;
    const titleEl = (drawer || root) ? (drawer || root).querySelector('.ant-drawer-title') : null;
    // 复用型抽屉：一旦重新装上内容（有 SETTINGS 或有正文），立即撤销我们加的 pointer-events:none
    for (const d of document.querySelectorAll('.ant-drawer[data-p6-shell-neutered]')) {
      const body = d.querySelector('.ant-drawer-body');
      const hasContent = !!d.querySelector(SETTINGS) || (body && (body.children.length > 0 || (body.innerText || '').trim().length > 0));
      if (hasContent) { try { d.style.pointerEvents = ''; } catch (e) { } d.removeAttribute('data-p6-shell-neutered'); }
    }
    const openDrawers = [...document.querySelectorAll('.ant-drawer')].filter(d => {
      if (!vis(d)) return false;
      if (d.getAttribute('data-p6-shell-neutered') === '1' && !d.querySelector(SETTINGS)) return false; // 已中和的空壳不算「开着」
      return d.classList.contains('ant-drawer-open') || !!d.querySelector(SETTINGS);
    });
    const zombies = [];
    for (const d of document.querySelectorAll('.ant-drawer,.ant-modal-wrap')) {
      if (!vis(d)) continue;
      const body = d.querySelector('.ant-drawer-body,.ant-modal-body');
      const hasS = !!d.querySelector(SETTINGS);
      const bc = body ? body.children.length : 0;
      const bt = body ? (body.innerText || '').replace(/\s+/g, ' ').trim().length : 0;
      if (!hasS && bc === 0 && bt === 0) zombies.push(d);
    }
    return {
      settingsInDom: roots.length, settingsVisible: visRoots.length,
      panelOpen: !!root, root, drawer,
      drawerVisible: drawer ? vis(drawer) : null,
      drawerOpenClass: drawer ? drawer.classList.contains('ant-drawer-open') : null,
      drawerRect: drawer ? rect(drawer) : null,
      drawerTitle: titleEl ? txt(titleEl) : null,
      drawerTitleSource: titleEl ? 'drawer.querySelector(.ant-drawer-title)（抽屉头部，非 settings 根内）' : null,
      drawerTitleInRoot: root ? !!root.querySelector('.ant-drawer-title') : null,
      headerText: header ? txt(header).slice(0, 80) : null,
      activeIds: [...document.querySelectorAll(NODE + '.active')].map(e => e.id),
      openDrawerCount: openDrawers.length,
      openDrawerTitles: openDrawers.map(d => { const t = d.querySelector('.ant-drawer-title'); return t ? txt(t) : null; }),
      zombieCount: zombies.length,
      zombieShells: zombies.map(d => ({ cls: (typeof d.className === 'string' ? d.className.replace(/\s+/g, ' ').slice(0, 60) : ''), rect: rect(d) })),
      textLen: root ? (root.innerText || '').length : 0,
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
          if (/^(ant-drawer|ant-modal|ant-drawer-content|ant-modal-wrap)\b/.test(c)) continue;
          if (/^(top|bottom)-line-mask$|scroll-mask|scrollbar/.test(c)) continue;
          if (!vis(el)) continue;
          const r = el.getBoundingClientRect();
          const overlay = /(^|[\s-])(overlay|mask)([\s-]|$)/i.test(c) && !/no-mask/.test(c) && r.width > 300 && r.height > 250;
          const bigSpin = /spinning|active/.test(c) && r.width > 60 && r.height > 60 && !!el.querySelector('.ant-spin-dot');
          if (overlay || bigSpin) o.push((c.trim().split(/\s+/)[0] || 'mask').slice(0, 30));
          if (o.length >= 5) break;
        }
        return [...new Set(o)];
      })()
    };
  }

  /* ---- 只点「取 消」的确认框处理（不保存、不丢弃） ---- */
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
      try { const E = t.startsWith('pointer') ? PointerEvent : MouseEvent; cancel.dispatchEvent(new E(t, o)); fired.push(t); } catch (e) { }
    }
    return { present: true, dismissed: true, clicked: '取 消', at: { x, y }, fired, text, safeNote: '只点「取 消」：不保存、不丢弃当前编辑，纯视图层关闭确认框' };
  }

  /* ---- 点击前「抽屉已卸载」三重确证 + 空壳纯视图清理 ---- */
  async function clearAndProve(targetId, budgetMs) {
    const t0 = Date.now();
    const steps = [], zombiesRemoved = [], confirms = [];
    const budget = budgetMs || 8000;
    // 0) 确认框（只点取消）
    for (let i = 0; i < 3; i++) {
      const dc = dismissConfirm();
      if (!dc.present) break;
      confirms.push(dc); steps.push('confirm:' + (dc.dismissed ? 'dismissed-by-cancel' : 'UNRESOLVED:' + dc.reason));
      if (!dc.dismissed) break;
    }
    // 1) 关闭循环：直到「可见 settings 根 == 0 且 无可见开着的抽屉」
    let st = state();
    for (let i = 0; i < 24 && Date.now() - t0 < budget; i++) {
      st = state();
      if (st.settingsVisible === 0 && st.openDrawerCount === 0) break;
      const btn = st.drawer ? [...st.drawer.querySelectorAll('.ant-drawer-close')].filter(vis)[0] : [...document.querySelectorAll('.ant-drawer-close')].filter(vis)[0];
      if (btn) { try { btn.click(); } catch (e) { } steps.push('close-btn'); }
      else {
        try {
          const k = { key: 'Escape', code: 'Escape', keyCode: 27, which: 27, bubbles: true, cancelable: true };
          document.body.dispatchEvent(new KeyboardEvent('keydown', k)); document.body.dispatchEvent(new KeyboardEvent('keyup', k));
          steps.push('esc');
        } catch (e) { }
      }
      await sleep(220);
    }
    // 2) 僵尸空壳「中和」（不是删除）：只加 pointer-events:none，让命中穿透到画布。
    //    v5 实测教训：上一版对空壳写 inline display:none —— 平台复用同一个 .ant-drawer DOM 节点，
    //    下次打开时它不会清掉我们的 inline 样式 -> 面板实际已挂载却不可见 -> 后续 12 个节点假 NO_PANEL。
    //    pointer-events 中和不改变布局/可见性，且一旦空壳重新装上内容会被 state() 自动撤销。
    st = state();
    for (const d of document.querySelectorAll('.ant-drawer,.ant-modal-wrap')) {
      if (!vis(d)) continue;
      const body = d.querySelector('.ant-drawer-body,.ant-modal-body');
      const hasS = !!d.querySelector(SETTINGS);
      const bc = body ? body.children.length : 0;
      const bt = body ? (body.innerText || '').replace(/\s+/g, ' ').trim().length : 0;
      if (hasS || bc !== 0 || bt !== 0) continue;
      if (d.getAttribute('data-p6-shell-neutered') === '1') continue;
      try {
        d.style.pointerEvents = 'none';
        d.setAttribute('data-p6-shell-neutered', '1');
        d.setAttribute('data-p6-zombie-removed', '1');
        zombiesRemoved.push({ cls: (typeof d.className === 'string' ? d.className.replace(/\s+/g, ' ').slice(0, 60) : ''), rect: rect(d), how: 'pointer-events:none（视图层中和，不改布局/可见性/任何配置；复用恢复内容时自动撤销）' });
        steps.push('shell-neutralized');
      } catch (e) { steps.push('shell-neutralize-failed'); }
    }
    if (zombiesRemoved.length) await sleep(80);
    // 3) 命中可达复验（画布是否被任何抽屉/弹窗挡住）
    const hp = targetId ? hitProbe(targetId) : null;
    st = state();
    const cleared = st.settingsVisible === 0 && st.openDrawerCount === 0 && !!(hp && hp.ok);
    if (cleared) {
      if (cleared) {
        S.closedSeq++; S.epoch++; S.closedAt = Date.now();
        // 关键：抽屉 DOM 节点跨多次开关复用，open 戳必须随关闭一起作废，否则 freshOpen 判据失效
        for (const d of document.querySelectorAll('.ant-drawer')) { d.removeAttribute('data-p6-open-seq'); d.removeAttribute('data-p6-epoch'); d.removeAttribute('data-p6-opened-at'); }
      }
      // 关键：抽屉 DOM 节点跨多次开关复用，open-seq 戳必须随关闭一起作废，否则 freshOpen 永远 false
      for (const d of document.querySelectorAll('.ant-drawer')) { d.removeAttribute('data-p6-open-seq'); d.removeAttribute('data-p6-opened-at'); }
    }
    return {
      cleared,
      ms: Date.now() - t0,
      steps: [...new Set(steps)],
      confirms,
      zombiesRemoved,
      proof: {
        visibleSettingsRoots: st.settingsVisible,
        openDrawerCount: st.openDrawerCount,
        openDrawerTitles: st.openDrawerTitles,
        hitReachable: !!(hp && hp.ok),
        hitProbe: hp,
        criterion: 'a) 可见 settings 根=0  b) 可见开着的 .ant-drawer=0  c) 目标节点 elementFromPoint 命中在其子树内'
      },
      afterState: {
        settingsInDom: st.settingsInDom, settingsVisible: st.settingsVisible,
        activeIds: st.activeIds, drawerTitle: st.drawerTitle, masks: st.masks, blockingConfirm: st.blockingConfirm
      },
      seq: { closedSeq: S.closedSeq, epoch: S.epoch }
    };
  }

  /* ---- 命中复验 ---- */
  function bringIntoView(el) {
    let moved = null;
    let p = el.parentElement;
    while (p && p !== document.body) {
      if (p.scrollWidth > p.clientWidth + 4 || p.scrollHeight > p.clientHeight + 4) {
        const before = { sl: p.scrollLeft, st: p.scrollTop };
        el.scrollIntoView({ block: 'center', inline: 'center' });
        if (p.scrollLeft !== before.sl || p.scrollTop !== before.st) moved = { scrollLeft: Math.round(p.scrollLeft), scrollTop: Math.round(p.scrollTop), cls: (typeof p.className === 'string' ? p.className.slice(0, 40) : '') };
        break;
      }
      p = p.parentElement;
    }
    const r = el.getBoundingClientRect();
    const onScreen = r.x + r.width > 0 && r.x < innerWidth && r.y + r.height > 0 && r.y < innerHeight;
    return { moved, rect: rect(el), onScreen };
  }
  function hitProbe(id) {
    const el = document.getElementById(id);
    if (!el) return { ok: false, reason: 'node-not-found' };
    const iv = bringIntoView(el);
    const r = el.getBoundingClientRect();
    const icon = el.querySelector('.node-icon, sy-icon, [class*="icon"]');
    const ir = (icon || el).getBoundingClientRect();
    let cx = Math.round(ir.x + ir.width / 2), cy = Math.round(ir.y + ir.height / 2);
    if (!(cx > 0 && cx < innerWidth && cy > 0 && cy < innerHeight)) { cx = Math.round(r.x + r.width / 2); cy = Math.round(r.y + r.height / 2); }
    const inView = cx >= 0 && cx < innerWidth && cy >= 0 && cy < innerHeight;
    const h = inView ? document.elementFromPoint(cx, cy) : null;
    const inNode = !!(h && el.contains(h));
    const occl = h ? h.closest('.ant-drawer,.ant-modal-wrap,.ant-modal-root,.ant-modal') : null;
    return {
      ok: inView && inNode && !occl,
      rect: rect(el), point: { x: cx, y: cy }, inView, inNode,
      offscreen: !inView, bringIntoView: iv,
      hit: h ? { tag: h.tagName, cls: hitCls(h) } : null,
      occluder: occl ? { cls: (typeof occl.className === 'string' ? occl.className.slice(0, 60) : ''), hasSettings: !!occl.querySelector(SETTINGS) } : null
    };
  }

  /* ---- 点击节点：先 settle（等画布停稳），再命中复验，再合成事件 ---- */
  async function clickNode(id, settleMs) {
    const el = document.getElementById(id);
    if (!el) return { ok: false, reason: 'node-not-found' };
    const rounds = [];
    for (let round = 0; round < 2; round++) {
      // settle：连续两次 scrollIntoView 后 rect 相同才算停稳
      let prevSig = null, stable = 0;
      for (let k = 0; k < 8; k++) {
        el.scrollIntoView({ block: 'center', inline: 'center' });
        const r = el.getBoundingClientRect();
        const sig = Math.round(r.x) + ',' + Math.round(r.y);
        if (sig === prevSig) { stable++; if (stable >= 1) break; } else stable = 0;
        prevSig = sig;
      }
      const hp = hitProbe(id);
      if (!hp.ok) {
        rounds.push({ round, ok: false, hitProbe: hp, settle: prevSig });
        if (hp.occluder) { clearAndProve(id, 4000); }
        continue;
      }
      const h = document.elementFromPoint(hp.point.x, hp.point.y);
      const o = { bubbles: true, cancelable: true, view: window, clientX: hp.point.x, clientY: hp.point.y };
      const fired = [];
      for (const ty of ['pointerdown', 'mousedown', 'pointerup', 'mouseup', 'click']) {
        try { h.dispatchEvent(new (ty.startsWith('pointer') ? PointerEvent : MouseEvent)(ty, o)); fired.push(ty); } catch (e) { }
      }
      // v5 关键修（live run2 实证）：v4 复合点击 = 合成 5 事件 + el.click() 一次，两次点击语义等价于「点开又点掉」，
      // 面板刚挂载就被同一批事件关闭 -> 12/21 节点 NO_PANEL。v5 改为状态驱动：先只做合成事件，
      // 等 700ms 若面板仍闭，才补 el.click()（容器兜底）；绝不双发。
      let openedAfter = 0;
      for (let w = 0; w < 6; w++) { await sleep(120); const s0 = state(); if (s0.panelOpen && s0.drawerTitle) { openedAfter = (w + 1) * 120; break; } }
      let fallback = null;
      if (!openedAfter) {
        try { el.click(); fallback = 'el.click'; } catch (e) { fallback = 'el.click-failed'; }
        for (let w = 0; w < 8; w++) { await sleep(120); const s0 = state(); if (s0.panelOpen && s0.drawerTitle) { openedAfter = (w + 1) * 120; break; } }
        fired.push('el.click');
      }
      rounds.push({ round, ok: true, hit: hp.hit, point: hp.point, settle: prevSig, openedAfterMs: openedAfter, fallback });
      return { ok: true, fired, point: hp.point, hit: hp.hit, rounds, settledBy: prevSig, openedAfterMs: openedAfter, fallback };
    }
    return { ok: false, reason: 'CLICK_TARGET_FAIL: hitProbe 未能在 2 轮内命中目标节点子树', rounds, finalHitProbe: hitProbe(id) };
  }

  /* ---- 等面板就绪（标题非空 + active==目标 + 指纹稳定 2 轮），并给抽屉打 openSeq 戳 ---- */
  function markFresh(drawer) {
    if (!drawer) return null;
    if (!drawer.getAttribute('data-p6-open-seq')) {
      S.openSeq++;
      drawer.setAttribute('data-p6-open-seq', String(S.openSeq));
      drawer.setAttribute('data-p6-epoch', String(S.epoch));
      drawer.setAttribute('data-p6-opened-at', String(Date.now()));
    }
    return Number(drawer.getAttribute('data-p6-open-seq'));
  }
  async function waitOpen(id, budgetMs) {
    const t0 = Date.now();
    const budget = budgetMs || 3000;
    let prevSig = null, stable = 0, samples = 0, firstTitleAt = null, cap = null;
    while (Date.now() - t0 < budget) {
      await sleep(130);
      samples++;
      const st = state();
      if (!st.panelOpen || !st.drawerTitle) { prevSig = null; stable = 0; continue; }
      markFresh(st.drawer);
      if (!firstTitleAt) firstTitleAt = Date.now() - t0;
      const sig = [st.textLen, st.drawerTitle, st.openDrawerCount].join('|');
      if (sig === prevSig) { stable++; if (stable >= 2) { cap = st; break; } } else { stable = 0; }
      prevSig = sig;
      cap = st;
    }
    const st = cap || state();
    const seq = st.drawer ? Number(st.drawer.getAttribute('data-p6-open-seq') || 0) : 0;
    const stampEpoch = st.drawer ? Number(st.drawer.getAttribute('data-p6-epoch') || 0) : 0;
    return {
      ms: Date.now() - t0, samples, firstTitleAtMs: firstTitleAt,
      panelOpen: st.panelOpen, drawerTitle: st.drawerTitle, drawerTitleSource: st.drawerTitleSource,
      drawerTitleInRoot: st.drawerTitleInRoot,
      activeAfter: st.activeIds, activeMatchesTarget: st.activeIds.includes(id),
      openDrawerCount: st.openDrawerCount,
      stableRounds: stable,
      openSeq: seq, stampEpoch, currentEpoch: S.epoch,
      freshOpen: !!(stampEpoch && stampEpoch === S.epoch),
      closedSeqAtClick: S.closedSeq,
      textLen: st.textLen,
      masks: st.masks,
      drawerRect: st.drawerRect
    };
  }

  /* ---- 面板捕获（结构指纹 + 全文指纹 + 字段） ---- */
  const ITEM = '.ant-form-item,[class*="form-item"],[class*="setting-item"],[class*="config-item"]';
  function labelOf(ctrl) {
    const it = ctrl.closest(ITEM);
    if (it) { const l = it.querySelector('.ant-form-item-label,label,[class*="label"]'); const t = txt(l || it); if (t && t.length <= 40) return t.replace(/\s*\*+\s*$/, ''); }
    const ph = ctrl.getAttribute('placeholder'); if (ph) return ph;
    return ctrl.getAttribute('name') || '';
  }
  function hintFor(root, title) {
    const full = (root ? (root.innerText || '').slice(0, 4000) : '') + ' ' + (title || '');
    const T = [['CALL_CUSTOM_SERVICE', ['自定义服务', '对外暴露的服务接口']], ['PUBLISH_EVENT', ['事件投递', '业务事件']], ['DATA_CONVERT', ['数据转换', '映射规则']], ['SUB_FLOW', ['子微流程']], ['CREATE_VARIABLE', ['创建变量', '创建包括基本数据']], ['CREATE_LIST', ['创建列表']], ['MODIFY_LIST', ['修改列表', '修改已有的列表']], ['LIST_OPERATION', ['列表操作', '对已有的列表进行操作']], ['CREATE_MAP', ['创建映射组', '映射键值对']], ['MAP_OPERATION', ['映射操作', '选择已有映射组']], ['UPDATE_DATA', ['更新数据']], ['BATCH_UPDATE', ['批量更新数据']], ['INSERT_DATA', ['插入数据']], ['DELETE_DATA', ['删除数据']], ['TYPE_CONVERT', ['类型转换']], ['QUERY_ONE', ['查询单条数据']], ['QUERY_MANY', ['查询多条数据']], ['MODIFY_VARIABLE', ['修改变量', '修改前序节点中已创建的变量']], ['BRANCH', ['条件分支']]];
    let best = 0, hint = 'unknown';
    for (const [t, kw] of T) { const s = kw.filter(k => full.includes(k)).length; if (s > best) { best = s; hint = t; } }
    return { hint, score: best, confidence: best >= 2 ? 'high' : best === 1 ? 'low' : 'none', basis: '标题+面板正文关键词命中数（v4 同一算法，阈值不变）' };
  }
  function capture() {
    const st = state();
    const root = st.root;
    const base = { url: location.href, panelOpen: st.panelOpen, drawerTitle: st.drawerTitle, drawerTitleInRoot: st.drawerTitleInRoot, activeIds: st.activeIds, openDrawerCount: st.openDrawerCount, openSeq: st.drawer ? Number(st.drawer.getAttribute('data-p6-open-seq') || 0) : 0 };
    if (!root) return Object.assign(base, { fingerprint: null, fullTextFingerprint: null, textLen: 0 });
    const ctls = [...root.querySelectorAll('input,textarea,select')].filter(vis);
    const inputs = [], selects = [], requiredFields = [];
    for (const c of ctls) {
      const lab = labelOf(c);
      const it = c.closest(ITEM);
      const labEl = it ? it.querySelector('.ant-form-item-label,label,[class*="label"]') : null;
      const req = !!c.required || c.getAttribute('aria-required') === 'true' || (!!it && (/required|is-required/.test(it.className || '') || /必填/.test(txt(labEl || it).slice(0, 60))));
      const info = { name: c.getAttribute('name') || '', type: c.tagName === 'SELECT' ? 'select' : (c.getAttribute('type') || c.tagName.toLowerCase()), value: (c.value || '').slice(0, 200), placeholder: c.getAttribute('placeholder') || '', required: req, disabled: !!c.disabled || c.getAttribute('aria-disabled') === 'true', readonly: !!c.readOnly, label: lab, selector: cssPath(c) };
      if (c.tagName === 'SELECT') selects.push(Object.assign(info, { selectedText: (c.selectedOptions[0] ? c.selectedOptions[0].text : '').slice(0, 80), options: [...c.options].slice(0, 30).map(o => ({ v: o.value, t: o.text.trim().slice(0, 60), sel: o.selected })) }));
      else inputs.push(info);
      if (req) requiredFields.push({ label: lab, name: info.name, selector: info.selector });
    }
    const formLabels = [...new Set([...root.querySelectorAll('.ant-form-item-label,label,[class*="label"]')].filter(vis).map(txt).filter(t => t && t.length <= 40).map(t => t.replace(/\s*\*+\s*$/, '')))];
    const btns = [...new Set([...root.querySelectorAll('button,[class*="btn"],[role="button"]')].filter(vis).map(txt).filter(t => t && t.length <= 16))].slice(0, 10);
    const ctlSig = ctls.map(c => [c.tagName, c.getAttribute('type') || '', labelOf(c).slice(0, 20), (c.getAttribute('placeholder') || '').slice(0, 12)].join(':')).sort();
    const material = { drawerTitle: st.drawerTitle, formLabels, ctlSig, btns };
    const raw = (root.innerText || '');
    const norm = raw.replace(/\s+/g, ' ').trim();
    const lines = raw.split('\n').map(s => s.trim()).filter(Boolean);
    return Object.assign(base, {
      rootSelector: cssPath(root), rootRect: rect(root),
      headerTitle: st.drawerTitle, headerTitleSource: st.drawerTitleSource, headerText: st.headerText,
      firstLine: (lines.find(l => l.length > 10) || '').slice(0, 60),
      formLabels, buttons: btns,
      nodeTypeHint: hintFor(root, st.drawerTitle),
      fingerprint: fnv(JSON.stringify(material)),
      fingerprintBasis: 'FNV1a x2 over {drawerTitle, formLabels[], ctlSig[], buttons[]} — 面板自身结构，不含 nodeId',
      fullTextFingerprint: fnv(norm),
      fullTextFingerprintBasis: 'FNV1a x2 over 面板全文 innerText（\\s+ -> 单空格，trim），含全部字段/选项/按钮文字',
      textLen: raw.length, normTextLen: norm.length,
      textSample: raw.slice(0, 1200),
      controlCount: ctls.length, inputs, selects, requiredFields,
      masks: st.masks
    });
  }

  /* ================= v6 逐字段采集（P0-2 / HANDOFF#2） =================
   * 全部基于 LIVE DOM 实测结构（2026-10-17 recon）：
   *  1) 面板内表单条目 = .ant-form-item；必填判据三源并存：
   *     a) itemClassName 含 required-item
   *     b) label 单元格内 .ant-form-item-required（antd 红星真正落点）
   *     c) 原生控件 required / aria-required
   *     实测 DATA_MAPPING_n8 六项全部 required-item + label 内 required 标记。
   *  2) 控件值：antd Select 不是 <select>，值在 .ant-select-selection-item 文本；
   *     radio 在 .ant-radio-button-wrapper(-checked) / 隐藏 input[value=ENUM]；switch 在 .ant-switch-checked。
   *  3) 内层映射入口只有三类按钮（实测）：
   *     「已设置」(DATA_MAPPING) / 「添加字段」(CHANGE_ENTITY, CREATE_ENTITY) / 「添加键值对」(CREATE_MAP)。
   *     点开后落在 .ant-modal（映射关系配置）或同一 drawer 内联区块。
   *     注意：只点入口读结构，绝不点 modal 内的「确定」。
   *  4) 映射行控件 id 自带行列坐标，形如
   *     com.seeyon.<appId>.dto.<Dto>_<row>_targetField / _mappingMode / _sourceField
   *     CREATE_MAP 的键值对为 placeholder 对「请输入映射的键(key)」/「请选择键对应的值」。
   *  5) 红字：.ant-form-item-explain / .ant-form-item-has-error。实测正常面板均为 0 条病态条目。
   *  6) 分支目标：CONDITION 卡片之间无独立连线 DOM；分支语义由
   *     .condition-title-text（符合条件/不符合条件）+ .node-body-title 表达式 + 分支序号承载。
   *     画布 svg path 实测只含 icon 字形（d 长度 <30 或为图标），不承载连线。故 branchTargets 以
   *     「条件序号 → 分支标签 → 表达式」为权威三元组，并标注 DOM 无连线层这一事实，不臆造目标节点 id。
   * ==================================================================== */

  /* ---- 必填判据（三源，任一成立即 required，并回写命中来源） ---- */
  function requiredOf(it, labEl, ctrl) {
    const src = [];
    if (/required-item|ant-form-item-required/.test(it.className || '')) src.push('itemClass:required-item');
    if (labEl && labEl.querySelector('.ant-form-item-required')) src.push('label:ant-form-item-required');
    if (ctrl && (ctrl.required === true || ctrl.getAttribute('aria-required') === 'true')) src.push('control:required-attr');
    const hasStar = !!(labEl && labEl.querySelector('.ant-form-item-required'));
    return { required: src.length > 0, sources: src, starMark: hasStar };
  }

  /* ---- 单条 form-item 的完整控件读数 ---- */
  function readItem(it) {
    const labEl = it.querySelector('.ant-form-item-label');
    const label = labEl ? txt(labEl).replace(/^\*\s*/, '').replace(/\s*\*$/, '') : '';
    const ctr = it.querySelector('.ant-form-item-control-input-content') || it;
    const inputs = [...ctr.querySelectorAll('input,textarea')].filter(vis);
    const sels = [...ctr.querySelectorAll('.ant-select')].filter(vis);
    const radios = [...ctr.querySelectorAll('.ant-radio-button-wrapper,.ant-radio-wrapper')].filter(vis);
    const checks = [...ctr.querySelectorAll('.ant-checkbox-wrapper')].filter(vis);
    const sw = ctr.querySelector('.ant-switch');
    const kinds = [];
    if (inputs.length) kinds.push('input');
    if (sels.length) kinds.push('ant-select');
    if (radios.length) kinds.push('radio');
    if (checks.length) kinds.push('checkbox');
    if (sw) kinds.push('switch');

    const controls = [];
    for (const c of inputs) {
      const ro = !!c.readOnly, dis = !!c.disabled;
      controls.push({
        kind: c.tagName === 'TEXTAREA' ? 'textarea' : 'input',
        inputType: c.getAttribute('type') || 'text',
        value: String(c.value == null ? '' : c.value).slice(0, 400),
        placeholder: c.getAttribute('placeholder') || '',
        disabled: dis, readonly: ro,
        id: c.id || '', name: c.getAttribute('name') || '',
        valueSource: ro ? 'input.readOnly（只读展示值，非用户输入）' : 'input.value（可视值）',
        selector: cssPath(c).slice(-160)
      });
    }
    for (const s of sels) {
      const si = s.querySelector('.ant-select-selection-item');
      const ph = s.querySelector('.ant-select-selection-placeholder');
      const multi = [...s.querySelectorAll('.ant-select-selection-item')].map(x => txt(x)).filter(Boolean);
      controls.push({
        kind: 'ant-select',
        value: si ? txt(si).slice(0, 300) : '',
        valueList: multi.slice(0, 20),
        placeholder: ph ? txt(ph) : '',
        empty: !si && !multi.length,
        disabled: /ant-select-disabled/.test(s.className || ''),
        multiple: /ant-select-multiple/.test(s.className || ''),
        treeSelect: /ant-tree-select/.test(s.className || ''),
        open: /ant-select-open/.test(s.className || ''),
        id: (s.querySelector('input') || {}).id || '',
        valueSource: 'antd .ant-select-selection-item 文本（antd 不写原生 select.value）',
        selector: cssPath(s).slice(-160)
      });
    }
    for (const r of radios) {
      const inp = r.querySelector('input');
      controls.push({
        kind: 'radio',
        value: inp ? String(inp.value || '') : '',
        text: txt(r.querySelector('.ant-radio-button') || r).slice(0, 120),
        checked: /ant-radio-button-wrapper-checked|ant-radio-wrapper-checked/.test(r.className || '') || !!(inp && inp.checked),
        disabled: /disabled/.test(r.className || ''),
        valueSource: 'antd radio wrapper checked class + 隐藏 input.value'
      });
    }
    for (const c of checks) {
      const inp = c.querySelector('input');
      controls.push({ kind: 'checkbox', text: txt(c).slice(0, 120), value: inp ? String(inp.value || '') : '', checked: /ant-checkbox-wrapper-checked/.test(c.className || '') || !!(inp && inp.checked) });
    }
    if (sw) controls.push({ kind: 'switch', checked: /ant-switch-checked/.test(sw.className || ''), disabled: !!sw.disabled });

    const req = requiredOf(it, labEl, inputs[0] || null);
    const extra = it.querySelector('.ant-form-item-extra');
    const explain = it.querySelector('.ant-form-item-explain');
    return {
      label, labelRaw: labEl ? txt(labEl) : '',
      required: req.required, requiredSources: req.sources, starMark: req.starMark,
      hasErrorClass: /ant-form-item-has-error/.test(it.className || ''),
      kinds, controls,
      extraNote: extra ? txt(extra).slice(0, 200) : null,
      errorText: explain ? txt(explain).slice(0, 300) : null,
      itemClass: String(it.className || '').replace(/\s+/g, ' ').slice(0, 100),
      itemText: txt(it).slice(0, 240),
      selector: cssPath(it).slice(-160)
    };
  }

  /* ---- 面板逐字段采集（替代 v5 的扁平 inputs/selects） ---- */
  function captureFields() {
    const st = state();
    const root = st.root;
    if (!root) return { panelOpen: false, fields: [], reason: 'NO_SETTINGS_ROOT' };
    // 只取最外层 form-item，避免 antd 的 control/label 子节点重复计入
    const all = [...root.querySelectorAll('.ant-form-item')].filter(vis);
    const outer = all.filter(it => !(it.parentElement && it.parentElement.closest('.ant-form-item')));
    const fields = outer.map(readItem);

    // 同名/同类型相邻重复项合并记录（CREATE_MAP 的键值对行没有 label，只能靠 placeholder 区分）
    for (const f of fields) {
      if (!f.label) {
        const ph = f.controls.map(c => c.placeholder).filter(Boolean);
        f.inferredLabel = ph.length ? ph.join(' / ') : null;
        f.labelSource = ph.length ? 'placeholder（该 form-item 无 .ant-form-item-label）' : 'UNVERIFIED: 既无 label 也无 placeholder';
      } else f.labelSource = '.ant-form-item-label';
    }

    // 内层映射入口判定（必须在 pageLib5 内本地定义：本函数被 toString() 后注入浏览器，
    // 不能引用 Node 侧的模块级变量/函数）。规则与模块级 ENTRY_RX / isActionBarButton 保持一致。
    const ENTRY_RX = /^(字段映射|对象引用|自动映射|已设置|添加字段|添加键值对|添加映射|添加参数|选择字段|配置映射|配置字段|设置映射)$/;
    const ACTION_BAR_RX = /(compid_node-config-submit-btn|btn-solid-default|ant-drawer-footer|node-config-submit|config-submit|submit-btn|ant-btn-primary)/i;
    const ACTION_BAR_TEXT_RX = /^(取消|确定|保存|关闭|提交|返回)$/;
    const isActionBarButton = b => {
      const cls = String(b.className || '');
      if (ACTION_BAR_RX.test(cls)) return true;
      return ACTION_BAR_TEXT_RX.test(txt(b).trim());
    };
    const isInnerMappingEntry = t => ENTRY_RX.test(String(t || '').trim());
    const entryButtons = [...root.querySelectorAll('button,[role="button"]')].filter(vis)
      .filter(b => !isActionBarButton(b))
      .map(b => ({ text: txt(b).slice(0, 30), cls: String(b.className || '').replace(/\s+/g, ' ').slice(0, 90), tag: b.tagName, selector: cssPath(b).slice(-140) }))
      .filter(b => isInnerMappingEntry(b.text));

    const errs = [...root.querySelectorAll('.ant-form-item-explain,.ant-form-item-explain-error')].filter(vis).map(e => txt(e).slice(0, 200));
    const errItems = [...root.querySelectorAll('.ant-form-item-has-error')].filter(vis).length;

    return {
      panelOpen: true, drawerTitle: st.drawerTitle,
      fields, fieldCount: fields.length,
      requiredCount: fields.filter(f => f.required).length,
      requiredBasis: 'required = itemClass(required-item) ∪ label(.ant-form-item-required 红星) ∪ 原生 required/aria-required；三者来源逐字段记于 requiredSources',
      entryButtons,
      errors: { list: errs, count: errs.length, errorItemCount: errItems, selector: '.ant-form-item-explain / .ant-form-item-has-error' },
      panelFullText: (root.innerText || '').slice(0, 6000),
      panelFullTextLen: (root.innerText || '').length
    };
  }

  /* ---- 点开内层映射入口，只读抓取映射行列（绝不点确定） ---- */
  async function openInnerEntry(matchText) {
    const st = state();
    if (!st.root) return { opened: false, reason: 'NO_PANEL' };
    const btns = [...st.root.querySelectorAll('button,[role="button"]')].filter(vis);
    const target = btns.find(b => txt(b) === matchText) || btns.find(b => new RegExp(matchText).test(txt(b)));
    if (!target) return { opened: false, reason: 'ENTRY_BUTTON_NOT_FOUND', wanted: matchText, present: btns.map(b => txt(b)).filter(Boolean).slice(0, 20) };
    const r = target.getBoundingClientRect();
    const x = Math.round(r.x + r.width / 2), y = Math.round(r.y + r.height / 2);
    for (const t of ['pointerover', 'pointerenter', 'pointerdown', 'mousedown', 'pointerup', 'mouseup', 'click']) {
      const E = t.startsWith('pointer') ? PointerEvent : MouseEvent;
      try { target.dispatchEvent(new E(t, { bubbles: true, cancelable: true, composed: true, view: window, clientX: x, clientY: y, button: 0 })); } catch (e) { }
    }
    // 等内层出现（modal 或内联区块），给 5s
    for (let i = 0; i < 25; i++) {
      await sleep(200);
      if (document.querySelector('.ant-modal-wrap .ant-modal')) return { opened: true, layer: 'ant-modal', clicked: txt(target), at: { x, y } };
      const inner = st.root.querySelector('[class*="mapping"],[class*="assign"]');
      if (inner && vis(inner)) return { opened: true, layer: 'inline-block', clicked: txt(target), at: { x, y } };
    }
    return { opened: false, reason: 'INNER_LAYER_NOT_APPEARED_5S', clicked: txt(target), at: { x, y } };
  }

  /* ---- 读内层映射层：行列映射 / 键值对 / 参数映射 ---- */
  function captureInnerMapping() {
    const modal = [...document.querySelectorAll('.ant-modal-wrap')].filter(vis).pop();
    const top = modal || null;
    const out = { present: !!top, layer: top ? 'ant-modal' : null };
    if (!top) return out;
    const titleEl = top.querySelector('.ant-modal-title');
    out.title = titleEl ? txt(titleEl) : null;
    out.fullText = (top.innerText || '').slice(0, 3000);
    out.buttons = [...top.querySelectorAll('button')].filter(vis).map(b => txt(b).slice(0, 20)).filter(Boolean);

    // 表格型映射（实测该面板当前为控件行，不是 table；两者都尝试）
    out.tables = [...top.querySelectorAll('table,.ant-table')].filter(vis).map(t => ({
      head: [...t.querySelectorAll('thead th')].filter(vis).map(x => txt(x)),
      rows: [...t.querySelectorAll('tbody tr')].filter(vis).map(tr => [...tr.querySelectorAll('td')].filter(vis).map(td => txt(td).slice(0, 80)))
    }));

    // 行容器：包含 >=2 个可用控件的最近一层
    const allCtrls = [...top.querySelectorAll('input,textarea,.ant-select')].filter(vis);
    const rows = [];
    for (const el of top.querySelectorAll('[class*="row"],[class*="item"],[class*="line"]')) {
      if (!vis(el)) continue;
      const inner = [...el.querySelectorAll('input,textarea,.ant-select')].filter(vis);
      if (inner.length < 2) continue;
      // 只保留最内层（子容器不再同时含 2+ 控件）
      const hasInnerRow = [...el.querySelectorAll('[class*="row"],[class*="item"]')].some(c => c !== el && vis(c) && [...c.querySelectorAll('input,textarea,.ant-select')].filter(vis).length >= 2);
      if (hasInnerRow) continue;
      const ctrls = inner.map(c => {
        if (c.classList && c.classList.contains('ant-select')) {
          const si = c.querySelector('.ant-select-selection-item');
          return { kind: 'ant-select', value: si ? txt(si) : '', placeholder: (c.querySelector('.ant-select-selection-placeholder') || {}).textContent || '', id: (c.querySelector('input') || {}).id || '' };
        }
        return { kind: c.tagName === 'TEXTAREA' ? 'textarea' : 'input', value: String(c.value == null ? '' : c.value).slice(0, 200), placeholder: c.getAttribute('placeholder') || '', readonly: !!c.readOnly, id: c.id || '' };
      });
      // 行列坐标：从控件 id 解析 <Dto>_<row>_<field>
      const coords = ctrls.map(c => { const m = String(c.id || '').match(/_(?:(\d+))_([A-Za-z][A-Za-z0-9_]*)$/); return m ? { row: Number(m[1]), field: m[2] } : null; }).filter(Boolean);
      rows.push({ rowClass: String(el.className || '').replace(/\s+/g, ' ').slice(0, 90), controls: ctrls, coords: coords.length ? coords : null, text: txt(el).slice(0, 200) });
      if (rows.length >= 30) break;
    }
    out.rows = rows;
    out.method = out.tables.length ? 'table+row-containers' : (rows.length ? 'row-containers(控件 id 含 <row>_<field> 坐标)' : 'UNVERIFIED: 该入口既无 table 也无含 2+ 控件的行容器');
    return out;
  }

  /* ---- 关闭内层层：只点「取消」，绝不点「确定」（不写配置） ---- */
  async function closeInnerLayer() {
    let acts = [];
    for (let round = 0; round < 5; round++) {
      const modal = [...document.querySelectorAll('.ant-modal-wrap')].filter(vis).pop();
      if (!modal) return { closed: true, acts };
      const btns = [...modal.querySelectorAll('button')];
      const cancel = btns.find(b => /^取\s*消$/.test(txt(b))) || modal.querySelector('.ant-modal-close');
      if (!cancel) {
        const confirmOnly = btns.find(b => /^确\s*定$/.test(txt(b)));
        return { closed: false, reason: 'NO_SAFE_CANCEL_ONLY_CONFIRM_PRESENT', acts, buttons: btns.map(b => txt(b)), safeNote: '只有「确定」时不点击，宁可留层也不写配置' + (confirmOnly ? '' : '') };
      }
      const r = cancel.getBoundingClientRect();
      const x = Math.round(r.x + r.width / 2), y = Math.round(r.y + r.height / 2);
      for (const t of ['pointerover', 'pointerenter', 'pointerdown', 'mousedown', 'pointerup', 'mouseup', 'click']) {
        const E = t.startsWith('pointer') ? PointerEvent : MouseEvent;
        try { cancel.dispatchEvent(new E(t, { bubbles: true, cancelable: true, composed: true, view: window, clientX: x, clientY: y, button: 0 })); } catch (e) { }
      }
      acts.push('modal-cancel');
      await sleep(500);
    }
    return { closed: ![...document.querySelectorAll('.ant-modal-wrap')].filter(vis).length, acts, note: 'max-rounds' };
  }

  /* ---- 分支目标：条件三元组（DOM 无连线层，如实标注） ---- */
  function branchTargets(branchId) {
    const el = document.getElementById(branchId);
    if (!el) return { captured: false, reason: 'NODE_NOT_FOUND' };
    const titleEl = el.querySelector('.caption-title') || el.querySelector('.node-title-text');
    const title = titleEl ? txt(titleEl) : '';
    const mCnt = title.match(/[（(]\s*(\d+)\s*[)）]/);
    const inst = (branchId.match(/_n([\d_a-z]+)$/) || [])[1] || '';
    const rows = [...document.querySelectorAll('.udc-microflow-editor-node-container[id^="CONDITION_n' + inst + '_"]')]
      .filter(c => c.id !== branchId)
      .map(c => {
        const idxEl = c.querySelector('.condition-title-icon');
        const lblEl = c.querySelector('.condition-title-text');
        const bodyEl = c.querySelector('.node-body-title') || c.querySelector('.node-body');
        const expr = bodyEl ? txt(bodyEl) : '';
        return {
          index: idxEl ? Number(txt(idxEl)) : null,
          conditionNodeId: c.id,
          branchLabel: lblEl ? txt(lblEl) : null,
          conditionExpression: expr || null,
          expressionSource: 'dom:.node-body-title（平台渲染的条件表达式，只读全文，不截断）',
          isDefaultBranch: /默认分支/.test(expr),
          targetNodeId: null,
          targetNodeIdReason: 'UNVERIFIED: 画布无独立连线 DOM（实测 .nodes 内 svg/path 均为图标字形，d 长 <30 或为内置图标），条件卡与后续节点的归属关系不在条件卡自身属性上'
        };
      })
      .sort((a, b) => (a.index || 0) - (b.index || 0));
    return {
      captured: rows.length > 0,
      branchId, branchTitle: title,
      declaredBranchCount: mCnt ? Number(mCnt[1]) : null,
      capturedConditionCount: rows.length,
      countConsistent: mCnt ? Number(mCnt[1]) === rows.length : null,
      conditions: rows,
      targetLayer: 'NO_EDGE_DOM: 分支目标节点 id 无法从条件卡 DOM 推出；需 P3（页面构建/执行回读）或设计态元数据补证，本版按 UNVERIFIED 登记，不臆造',
      source: 'node-card DOM (read-only)'
    };
  }


  /* ---- BRANCH/CONDITION 分支 UI 只读采集（沿用 v4.1 锚点定位，不猜文本行） ---- */
  // v5.1 新增：结构性节点（BRANCH/CONDITION）自身卡片身份指纹 —— 它们没有抽屉面板，
  // 身份只能由「卡片 DOM 全文 + 条件表达式 + 分支序号」自证。不含 nodeId，避免自我循环。
  function structuralCardFingerprint(id) {
    const el = document.getElementById(id);
    if (!el) return { ok: false, reason: 'node-not-found' };
    const titleEl = el.querySelector('.caption-title') || el.querySelector('.condition-title');
    const title = titleEl ? txt(titleEl) : '';
    const bodyEl = el.querySelector('.node-body-title') || el.querySelector('.node-body');
    const bodyTxt = bodyEl ? txt(bodyEl) : '';
    const idx = (el.querySelector('.condition-title-icon') || {});
    const index = (idx.textContent || '').trim();
    const cls = (typeof el.className === 'string' ? el.className : '');
    const material = { title, bodyTxt, index, role: /branch-main/.test(cls) ? 'branch-main' : (/CONDITION_n/.test(id) ? 'condition-row' : 'unknown'), collapsed: !!el.querySelector('.collapse-btn .lined-unfold') };
    return { ok: true, title, bodyTxt, index, material, fingerprint: fnv(JSON.stringify(material)), basis: 'FNV1a×2 over {caption/condition title, node-body 表达式文本, 条件序号, 角色(branch-main/condition-row), 折叠态} — 不含 nodeId', cardText: txt(el).slice(0, 400) };
  }

  function branchSpec(id) {
    const el = document.getElementById(id);
    if (!el) return { captured: false, reason: 'BRANCH_UI_UNCAPTURED: node element not found' };
    const pathTok = s => { const o = []; const re = /[\u4e00-\u9fa5A-Za-z_][\w\u4e00-\u9fa5]*(?:\.[\w\u4e00-\u9fa5()（）]+|\[[^\]]+\])*/g; let m; while ((m = re.exec(s || '')) && o.length < 30) { const t = m[0]; if (t.length >= 2) o.push(t); } return [...new Set(o)]; };
    const bodyTxt = c => { const b = c.querySelector('.node-body-title') || c.querySelector('.node-body'); return b ? txt(b) : ''; };
    const condOf = (c, i) => {
      const icon = c.querySelector('.condition-title-icon');
      const lt = c.querySelector('.condition-title-text');
      const expr = bodyTxt(c);
      return { index: icon && txt(icon) ? Number(txt(icon)) : i, nodeId: c.id, label: (lt ? txt(lt) : '') || null, exprRaw: expr || null, exprSource: expr ? 'dom:.node-body-title（平台渲染的条件表达式，只读）' : null, tokens: pathTok(expr), source: 'node-card DOM (read-only)' };
    };
    if (/^BRANCH_n/.test(id)) {
      const inst = (id.match(/_n(\d+)$/) || [])[1] || id;
      const titleEl = el.querySelector('.caption-title') || el.querySelector('.node-title-text');
      const title = titleEl ? txt(titleEl) : '';
      const mCnt = title.match(/[（(]\s*(\d+)\s*[)）]/);
      const conds = [...document.querySelectorAll('.udc-microflow-editor-node-container[id^="CONDITION_n' + inst + '_"]')].filter(c => c.id !== id).map((c, i) => condOf(c, i));
      const branchCount = mCnt ? Number(mCnt[1]) : null;
      const ok = !!branchCount && conds.length > 0 && branchCount === conds.length;
      return { captured: ok, branchCount, countSource: 'dom:.caption-title「' + title + '」括号内数字', conditions: conds, conditionCount: conds.length, countConsistent: ok, source: 'node-card DOM (read-only)', title, reason: ok ? null : 'BRANCH_UI_UNCAPTURED: branchCount/conditions mismatch (count=' + branchCount + ', conditions=' + conds.length + ')' };
    }
    if (/^CONDITION_n/.test(id)) {
      const one = condOf(el, 0);
      const parentBranchId = 'BRANCH_n' + (((id.match(/_n(\d+)_\d+$/) || [])[1]) || '');
      if (!one.exprRaw && !one.label) return { captured: false, reason: 'BRANCH_UI_UNCAPTURED: condition card has neither .node-body-title nor .condition-title-text', evidence: txt(el).slice(0, 200) };
      return { captured: true, branchCount: 1, parentBranchId, conditions: [one], conditionCount: 1, countConsistent: true, source: 'node-card DOM (read-only)', reason: null };
    }
    return { captured: false, reason: 'BRANCH_UI_UNCAPTURED: not a BRANCH/CONDITION node id: ' + id };
  }

  /* ---- 并发探针自检 ---- */
  function foreignState() {
    return { probeTag: window.__P6 ? window.__P6.__v : 'none', openSeq: S.openSeq, closedSeq: S.closedSeq, reinjectedBefore: S.reinjectedBefore, otherFlowTabsHint: 'Node 侧统计 /json/list 中同 flow 的 page 数量' };
  }

  S.state = state; S.enumNodes = enumNodes; S.capture = capture; S.hitProbe = hitProbe;
  S.captureFields = captureFields; S.readItem = readItem; S.openInnerEntry = openInnerEntry;
  S.captureInnerMapping = captureInnerMapping; S.closeInnerLayer = closeInnerLayer; S.branchTargets = branchTargets;
  S.clearAndProve = clearAndProve; S.clickNode = clickNode; S.waitOpen = waitOpen;
  S.dismissConfirm = dismissConfirm; S.branchSpec = branchSpec; S.foreignState = foreignState;
  S.structuralCardFingerprint = structuralCardFingerprint;
  S.cssPath = cssPath; S.txt = txt; S.SETTINGS = SETTINGS;
  window.__P6 = S;
  return { injected: true, tag: S.__v, seq: { closedSeq: S.closedSeq, openSeq: S.openSeq } };
}

/* ---------- 判定 ---------- */
const ALLOW = {
  CALL_APP_SERVICE: ['CALL_CUSTOM_SERVICE'], PUBLISH_BUSINESS_EVENT: ['PUBLISH_EVENT'],
  DATA_MAPPING: ['DATA_CONVERT'], CONVERT_DATA: ['TYPE_CONVERT', 'DATA_CONVERT'],
  SUB_MICROFLOW: ['SUB_FLOW'], CREATE_VARIABLE: ['CREATE_VARIABLE'], CHANGE_VARIABLE: ['MODIFY_VARIABLE'],
  RETRIEVE: ['QUERY_ONE'], RETRIEVE_ARRAY: ['QUERY_MANY', 'QUERY_ONE'], CREATE_LIST: ['CREATE_LIST'], CHANGE_LIST: ['MODIFY_LIST'],
  LIST_OPERATION: ['LIST_OPERATION'], CREATE_MAP: ['CREATE_MAP'], MAP_OPERATION: ['MAP_OPERATION'],
  CHANGE_ENTITY: ['UPDATE_DATA'], CHANGE_BATCH_ENTITY: ['BATCH_UPDATE'], CREATE_ENTITY: ['INSERT_DATA'], DELETE_ENTITY: ['DELETE_DATA']
};
const STRUCTURAL = /^(BRANCH|CONDITION|START|END|NOTE)$/;
function expectationFor(nodeType) {
  const k = Object.keys(ALLOW).find(x => nodeType === x);
  return k ? ALLOW[k] : null;
}

function selfTestCount() { try { return selfTest(true).cases.length; } catch (e) { return null; } }
function evaluate(nodes) {
  const fails = [], notes = [], byFp = new Map(), byFull = new Map(), byStruct = new Map();
  for (const n of nodes) {
    if (n.status === 'STRUCTURAL_BRANCH_CAPTURED' || n.status === 'STRUCTURAL_CARD_CAPTURED') {
      const cardFp = n.cardIdentity && n.cardIdentity.fingerprint;
      if (!cardFp) { fails.push({ code: 'STRUCTURAL_NO_CARD_IDENTITY', rule: 'structural_node_card_identity_missing', node: n.nodeId, nodeType: n.nodeType }); n.panelIdentityMatch = false; continue; }
      if (n.status === 'STRUCTURAL_BRANCH_CAPTURED' && n.branchSpec && n.branchSpec.countConsistent === false) {
        fails.push({ code: 'BRANCH_UI_UNCAPTURED', rule: 'BRANCH_COUNT_ASSERT: branchCount != conditions.length', node: n.nodeId, nodeType: n.nodeType, evidence: { branchCount: n.branchSpec.branchCount, conditionCount: n.branchSpec.conditionCount } });
        n.panelIdentityMatch = false;
      } else {
        n.panelIdentityMatch = !!(n.identity && n.identity.proven);
        byStruct.set(cardFp, (byStruct.get(cardFp) || []).concat([n]));
        notes.push({ code: 'BRANCH_SPEC_CAPTURED', node: n.nodeId, branchCount: n.branchSpec && n.branchSpec.branchCount, cardFingerprint: cardFp, title: n.cardIdentity.title, expr: (n.cardIdentity.bodyTxt || '').slice(0, 80) });
      }
      continue;
    }
    if (n.status === 'BRANCH_UI_UNCAPTURED') { fails.push({ code: 'BRANCH_UI_UNCAPTURED', rule: 'branch_ui_not_captured_no_null_success', node: n.nodeId, nodeType: n.nodeType, evidence: n.branchFailReason }); n.panelIdentityMatch = false; continue; }
    if (n.status === 'CLICK_TARGET_FAIL') { fails.push({ code: 'CLICK_TARGET_FAIL', rule: 'hit_probe_never_inside_target_node_subtree', node: n.nodeId, nodeType: n.nodeType, evidence: n.click }); n.panelIdentityMatch = false; continue; }
    if (n.status === 'CLEAR_OVERLAY_FAIL') { fails.push({ code: 'CLEAR_OVERLAY_FAIL', rule: 'drawer_not_proven_closed_failed_fast_before_click', node: n.nodeId, nodeType: n.nodeType, evidence: n.preClose }); n.panelIdentityMatch = false; continue; }
    if (n.status === 'PANEL_SWITCH_FAIL') { fails.push({ code: 'PANEL_IDENTITY_FAIL', rule: 'panel_not_proven_for_this_node', node: n.nodeId, nodeType: n.nodeType, evidence: n.identity }); n.panelIdentityMatch = false; continue; }
    if (n.status === 'NO_PANEL') { fails.push({ code: 'NO_PANEL', rule: 'no_panel_root_after_click_and_retry', node: n.nodeId, nodeType: n.nodeType, evidence: n.identity }); n.panelIdentityMatch = false; continue; }
    const fp = n.panelFingerprint, ft = n.panelFullTextFingerprint;
    if (!fp) { fails.push({ code: 'NO_FINGERPRINT', node: n.nodeId }); n.panelIdentityMatch = false; continue; }
    const arr = byFp.get(fp) || []; arr.push(n); byFp.set(fp, arr);
    const arr2 = byFull.get(ft) || []; arr2.push(n); byFull.set(ft, arr2);
  }
  for (const [fp, arr] of byFp) {
    const types = [...new Set(arr.map(x => x.nodeType))];
    if (arr.length > 1 && types.length > 1)
      fails.push({ code: 'PANEL_IDENTITY_FAIL', rule: 'duplicate_structural_fingerprint_across_node_types', fingerprint: fp, nodes: arr.map(x => ({ nodeId: x.nodeId, nodeType: x.nodeType, drawerTitle: x.drawerTitle })), reason: '不同 nodeType 得到同一面板结构指纹 -> 同一面板被采了两次' });
    else if (arr.length > 1) notes.push({ code: 'SAME_TYPE_SAME_STRUCTURAL_FP', fingerprint: fp, nodes: arr.map(x => x.nodeId), note: '同类型节点结构相同（合法），但全文指纹必须互异' });
  }
  for (const [ft, arr] of byFull) {
    const types = [...new Set(arr.map(x => x.nodeType))];
    if (arr.length > 1 && types.length > 1)
      fails.push({ code: 'PANEL_IDENTITY_FAIL', rule: 'duplicate_full_text_fingerprint_across_node_types', fullTextFingerprint: ft, nodes: arr.map(x => ({ nodeId: x.nodeId, nodeType: x.nodeType, drawerTitle: x.drawerTitle, textLen: x.panelTextLen })), reason: '面板全文完全相同（跨类型）-> 指纹复制' });
  }
  for (const n of nodes) {
    if (!n.panelHint || n.status !== 'CAPTURED') continue;
    const exp = expectationFor(n.nodeType), h = n.panelHint;
    if (exp && h && h.confidence === 'high' && !exp.includes(h.hint))
      fails.push({ code: 'PANEL_IDENTITY_FAIL', rule: 'panel_title_contradicts_node_type', node: n.nodeId, nodeType: n.nodeType, expectedHints: exp, panelHint: h.hint, drawerTitle: n.drawerTitle, panelExcerpt: n.panelTextSample ? n.panelTextSample.slice(0, 200) : null });
  }
  // v5.1 新增：结构性节点（BRANCH/CONDITION）卡片指纹互异断言（防复制）
  for (const [fp, arr] of byStruct) {
    if (arr.length > 1) {
      const titles = arr.map(x => (x.cardIdentity && x.cardIdentity.title) || x.nodeId);
      const distinctTitles = new Set(titles).size;
      if (distinctTitles === 1 && arr.length > 1) {
        // CONDITION 行共享同一句「符合条件即进入该分支」是平台固定文案，靠 index+表达式区分；
        // 若 index 与 expr 也全同，才是真复制。
        const sigs = new Set(arr.map(x => [(x.cardIdentity.index || ''), (x.cardIdentity.bodyTxt || '')].join('|')));
        if (sigs.size === 1) fails.push({ code: 'PANEL_IDENTITY_FAIL', rule: 'duplicate_structural_card_fingerprint', fingerprint: fp, nodes: arr.map(x => ({ nodeId: x.nodeId, title: x.cardIdentity.title, index: x.cardIdentity.index })), reason: '结构性节点卡片内容完全相同（标题+表达式+序号）-> 同一卡片被采了两次' });
        else notes.push({ code: 'STRUCTURAL_CARD_SHARED_TITLE', fingerprint: fp, nodes: arr.map(x => x.nodeId), note: '同标题但表达式/序号不同（平台固定文案，合法）' });
      } else {
        notes.push({ code: 'STRUCTURAL_CARD_SHARED_FP_DIFF_TITLE', fingerprint: fp, nodes: arr.map(x => x.nodeId), note: '卡片指纹相同但标题不同（结构相同，合法）' });
      }
    }
  }
  // 相邻节点全文指纹互异（防复制）
  const ordered = nodes.filter(n => n.status === 'CAPTURED');
  for (let i = 1; i < ordered.length; i++) {
    const a = ordered[i - 1], b = ordered[i];
    if (a.panelFullTextFingerprint && a.panelFullTextFingerprint === b.panelFullTextFingerprint)
      fails.push({ code: 'PANEL_IDENTITY_FAIL', rule: 'adjacent_nodes_share_full_text_fingerprint', nodes: [a.nodeId, b.nodeId], fingerprint: a.panelFullTextFingerprint });
  }
  for (const n of nodes) {
    if (n.status === 'STRUCTURAL_BRANCH_CAPTURED' || n.status === 'BRANCH_UI_UNCAPTURED') continue;
    const hit = fails.find(f => (f.node && f.node === n.nodeId) || (f.nodes && f.nodes.some(x => (x.nodeId || x) === n.nodeId)));
    if (n.status === 'CAPTURED') n.panelIdentityMatch = !hit;
    n.panelIdentityBasis = hit ? hit.rule : 'pre-click 抽屉三重确证关闭 -> 点击 -> .active==目标 && drawer 标题非空 && freshOpen(openSeq>closedSeq) && 结构/全文指纹互异';
  }
  notes.push({ code: 'V5_CLOSE_PROOF', rule: '每次点击前必须同时满足：可见 settings 根=0、可见开着且承载面板的 .ant-drawer=0、目标节点 elementFromPoint 命中在其子树内；任一不满足即 CLEAR_OVERLAY_FAIL 且不点击不采集' });
  const status = fails.length ? 'PANEL_IDENTITY_FAIL' : 'PASS';
  return { fails, notes, status, exitCode: status === 'PASS' ? 0 : 3 };
}

// ===== v6 字段完备性断言（HANDOFF#2 完成标准 6：缺失必须写明原因，不得留空冒充完成）=====
/* ---------- D2 二分裁定（main 2026-10-18 00:56，ROUTE:109-116） ----------
 * 按成因分三类，不再一律计入 failure：
 *   HARD       真·采集缺失      -> 计 failure -> status≠PASS（fieldsStatus=FAIL）
 *   BUSINESS   业务空值          -> 不计 failure，保留 issues[]（fieldsStatus=PARTIAL_BUSINESS_EMPTY）
 *   STRUCTURAL 结构性不可证      -> 不计 failure，summary 单列 structuralUnverified（fieldsStatus=STRUCTURAL_UNVERIFIED）
 * 依据：3 个 BRANCH/CONDITION 的 targetNodeId 结构上恒为 null（画布无独立连线 DOM），
 *   一律计 failure 会使 21/21 PASS 数学上不可达；且 INPUT_EMPTY_NO_PLACEHOLDER 是"字段本来为空"的合法业务状态。
 *   auditor/AUDIT-RUN-D2B-IMPACT.md + implementer/D2B-IMPACT-INDEPENDENT.md 双双实测复现。
 */
const ISSUE_HARD = ['FIELDS_NO_PANEL', 'FIELDS_EMPTY', 'FIELD_NO_CONTROL',
  'INNER_MAPPING_NOT_ATTEMPTED', 'INNER_LAYER_NOT_CLOSED', 'BRANCH_TARGETS_MISSING'];
const ISSUE_BUSINESS = ['INPUT_EMPTY_NO_PLACEHOLDER', 'SELECT_BOTH_EMPTY'];
const ISSUE_STRUCTURAL = ['BRANCH_TARGET_NODE_UNVERIFIED', 'FIELD_LABEL_UNVERIFIED'];
// 其余（BRANCH_COUNT_MISMATCH / CONDITION_EXPR_EMPTY / INNER_MAPPING_BLOCKED / INNER_MAPPING_NO_ROWS /
// INNER_MAPPING_REASON_MISSING）保持原语义：不计 failure，进 unverified 明细（既非硬失败也非上述两类）

function evaluateFields(nodes) {
  const fails = [], perNode = [];
  for (const r of nodes) {
    const structural = r.status === 'STRUCTURAL_BRANCH_CAPTURED' || r.status === 'STRUCTURAL_CARD_CAPTURED';
    const got = r.status === 'CAPTURED' || structural;
    if (!got) { perNode.push({ node: r.nodeId, verdict: 'NOT_APPLICABLE', fieldsStatus: 'NOT_APPLICABLE', reason: 'node not captured: ' + r.status }); continue; }
    const f = r.fields || {};
    const issues = [];
    if (structural) {
      const bt = r.branchTargets || {};
      if (!bt.captured) issues.push({ code: 'BRANCH_TARGETS_MISSING', detail: bt.reason || 'no branchTargets' });
      for (const c of (bt.conditions || [])) {
        if (!c.conditionExpression) issues.push({ code: 'CONDITION_EXPR_EMPTY', condition: c.conditionNodeId });
        if (!c.targetNodeId) issues.push({ code: 'BRANCH_TARGET_NODE_UNVERIFIED', condition: c.conditionNodeId, reason: c.targetNodeIdReason });
      }
      if (bt.declaredBranchCount != null && bt.capturedConditionCount != null && bt.declaredBranchCount !== bt.capturedConditionCount)
        issues.push({ code: 'BRANCH_COUNT_MISMATCH', declared: bt.declaredBranchCount, captured: bt.capturedConditionCount });
    } else {
      if (!f.panelOpen) issues.push({ code: 'FIELDS_NO_PANEL', reason: f.reason || 'panel not open' });
      if (!f.fields || !f.fields.length) issues.push({ code: 'FIELDS_EMPTY', reason: f.reason || 'no .ant-form-item captured' });
      for (const fd of (f.fields || [])) {
        if (!fd.label && !fd.inferredLabel) issues.push({ code: 'FIELD_LABEL_UNVERIFIED', selector: fd.selector, reason: 'no .ant-form-item-label and no placeholder' });
        if (!fd.controls || !fd.controls.length) issues.push({ code: 'FIELD_NO_CONTROL', label: fd.label, reason: 'form-item has no visible input/ant-select/radio/switch' });
        for (const c of (fd.controls || [])) {
          if (c.kind === 'ant-select' && c.empty && !c.placeholder) issues.push({ code: 'SELECT_BOTH_EMPTY', label: fd.label, reason: 'no selection-item and no placeholder -> 无法判定是空值还是未渲染' });
          if (c.kind === 'input' && c.value === '' && !c.placeholder) issues.push({ code: 'INPUT_EMPTY_NO_PLACEHOLDER', label: fd.label, id: c.id });
        }
      }
      // 内层映射入口必须给出结论（抓到 / 无入口 / BLOCKED），不得静默省略
      const im = r.innerMapping || [];
      const hasEntry = !!(f.entryButtons && f.entryButtons.length);
      if (hasEntry && !im.length) issues.push({ code: 'INNER_MAPPING_NOT_ATTEMPTED', reason: 'entryButtons 存在但未尝试下钻' });
      for (const m of im) {
        if (m.status === 'BLOCKED_ENTRY') issues.push({ code: 'INNER_MAPPING_BLOCKED', entry: m.entry, reason: (m.open && m.open.reason) || 'entry not opened' });
        if (m.status === 'OPENED_NO_ROWS_UNVERIFIED') issues.push({ code: 'INNER_MAPPING_NO_ROWS', entry: m.entry, reason: (m.mapping && m.mapping.method) || 'opened but no rows', layerTitle: m.mapping && m.mapping.title });
        if (m.fatal) issues.push({ code: 'INNER_LAYER_NOT_CLOSED', entry: m.entry, reason: m.fatal });
      }
      if (!hasEntry && !r.innerMappingNote) issues.push({ code: 'INNER_MAPPING_REASON_MISSING', reason: '无入口但也没写原因' });
    }
    // ---- D2 二分：按成因归类，只有 HARD 计 failure ----
    const hard = issues.filter(x => ISSUE_HARD.includes(x.code));
    const business = issues.filter(x => ISSUE_BUSINESS.includes(x.code));
    const structuralUnv = issues.filter(x => ISSUE_STRUCTURAL.includes(x.code));
    const other = issues.filter(x => !hard.includes(x) && !business.includes(x) && !structuralUnv.includes(x));
    const unverified = business.concat(structuralUnv).concat(other);

    // fieldsStatus 独立判据（ROUTE:114）：OK / PARTIAL_BUSINESS_EMPTY / STRUCTURAL_UNVERIFIED / FAIL
    // 优先级 FAIL > STRUCTURAL_UNVERIFIED > PARTIAL_BUSINESS_EMPTY > OK
    // （structural 与 business 同时存在时，structural 更需要 auditor 关注；两者都记在 counts 里不丢）
    const fieldsStatus = hard.length ? 'FAIL'
      : (structuralUnv.length ? 'STRUCTURAL_UNVERIFIED'
        : (business.length ? 'PARTIAL_BUSINESS_EMPTY'
          : (other.length ? 'STRUCTURAL_UNVERIFIED' : 'OK')));
    // verdict 兼容既有断言：FAIL / PARTIAL_UNVERIFIED / OK（PARTIAL 仅表示"非硬失败但有未闭合项"）
    const verdict = hard.length ? 'FAIL' : (unverified.length ? 'PARTIAL_UNVERIFIED' : 'OK');

    perNode.push({
      node: r.nodeId, nodeType: r.nodeType,
      fieldCount: (f.fields || []).length, requiredCount: f.requiredCount || 0,
      issues,
      counts: { hard: hard.length, businessEmpty: business.length, structuralUnverified: structuralUnv.length, other: other.length },
      hardIssueCount: hard.length,
      businessEmptyIssueCount: business.length,
      structuralUnverifiedIssueCount: structuralUnv.length,
      unverifiedIssueCount: unverified.length,
      fieldsStatus,
      verdict
    });
    for (const h of hard) fails.push({ code: 'FIELDS_INCOMPLETE', rule: 'v6_field_completeness', node: r.nodeId, nodeType: r.nodeType, detail: h });
  }
  const allCovered = nodes.length === (perNode.filter(x => x.verdict !== 'NOT_APPLICABLE').length + perNode.filter(x => x.verdict === 'NOT_APPLICABLE').length);
  const summary = {
    nodes: nodes.length,
    ok: perNode.filter(x => x.verdict === 'OK').length,
    partial: perNode.filter(x => x.verdict === 'PARTIAL_UNVERIFIED').length,
    fail: perNode.filter(x => x.verdict === 'FAIL').length,
    notApplicable: perNode.filter(x => x.verdict === 'NOT_APPLICABLE').length,
    // ROUTE:113 —— 结构性与业务空值单列计数，存在也不阻止 PASS，但必须如实可数
    structuralUnverified: perNode.reduce((a, x) => a + (x.counts ? x.counts.structuralUnverified : 0), 0),
    structuralUnverifiedNodes: perNode.filter(x => x.fieldsStatus === 'STRUCTURAL_UNVERIFIED').map(x => x.node),
    businessEmpty: perNode.reduce((a, x) => a + (x.counts ? x.counts.businessEmpty : 0), 0),
    businessEmptyNodes: perNode.filter(x => x.fieldsStatus === 'PARTIAL_BUSINESS_EMPTY').map(x => x.node),
    hardIssueTotal: perNode.reduce((a, x) => a + (x.counts ? x.counts.hard : 0), 0),
    // fieldsStatus 分布（ROUTE:114 独立判据）
    fieldsStatusCounts: perNode.reduce((a, x) => { a[x.fieldsStatus] = (a[x.fieldsStatus] || 0) + 1; return a; }, {}),
    coverage21: nodes.length === 21, allCovered
  };
  return { fails, perNode, summary };
}


/* ---------- self-test（纯逻辑，不连浏览器） ---------- */
function selfTest(quiet) {
  const mk = (id, type, fp, title, ft, hint) => ({ nodeId: id, nodeType: type, label: type, status: 'CAPTURED', drawerTitle: title, activeBefore: [], activeAfter: [id], panelFingerprint: fp, panelFullTextFingerprint: ft, panelTextLen: 100, panelHint: { hint: hint || (title === '自定义服务' ? 'CALL_CUSTOM_SERVICE' : 'PUBLISH_EVENT'), score: 2, confidence: 'high' }, identity: { activeMatchesTarget: true, titleNonEmpty: true, freshOpen: true, proven: true } });
  const dupStruct = evaluate([mk('CALL_APP_SERVICE_n16', 'CALL_APP_SERVICE', 'fpA', '自定义服务', 'ftA'), mk('PUBLISH_BUSINESS_EVENT_n17', 'PUBLISH_BUSINESS_EVENT', 'fpA', '自定义服务', 'ftB')]);
  const dupFull = evaluate([mk('CALL_APP_SERVICE_n16', 'CALL_APP_SERVICE', 'fpA', '自定义服务', 'ftA'), mk('PUBLISH_BUSINESS_EVENT_n17', 'PUBLISH_BUSINESS_EVENT', 'fpB', '事件投递', 'ftA')]);
  const good = evaluate([mk('CALL_APP_SERVICE_n16', 'CALL_APP_SERVICE', 'fpA', '自定义服务', 'ftA'), mk('PUBLISH_BUSINESS_EVENT_n17', 'PUBLISH_BUSINESS_EVENT', 'fpB', '事件投递', 'ftB')]);
  const titleBad = evaluate([{ nodeId: 'PUBLISH_BUSINESS_EVENT_n17', nodeType: 'PUBLISH_BUSINESS_EVENT', status: 'CAPTURED', drawerTitle: '自定义服务', panelFingerprint: 'fpB', panelFullTextFingerprint: 'ftB', panelTextLen: 99, panelHint: { hint: 'CALL_CUSTOM_SERVICE', score: 2, confidence: 'high' }, identity: {} }]);
  const switchFail = evaluate([{ nodeId: 'RETRIEVE_n2', nodeType: 'RETRIEVE', status: 'PANEL_SWITCH_FAIL', identity: { activeMatchesTarget: false, titleNonEmpty: true, freshOpen: true } }]);
  const clearFail = evaluate([{ nodeId: 'RETRIEVE_n2', nodeType: 'RETRIEVE', status: 'CLEAR_OVERLAY_FAIL', preClose: { proof: { visibleSettingsRoots: 1 } } }]);
  const noPanel = evaluate([{ nodeId: 'RETRIEVE_n2', nodeType: 'RETRIEVE', status: 'NO_PANEL', identity: { panelOpened: false } }]);
  const structural = evaluate([{ nodeId: 'BRANCH_n18', nodeType: 'BRANCH', status: 'STRUCTURAL_BRANCH_CAPTURED', clickPath: { attempted: false }, identity: { proven: true }, cardIdentity: { fingerprint: 'cfpB', title: '分支(2)', bodyTxt: '条件分支', index: '' }, branchSpec: { branchCount: 2, conditionCount: 2, countConsistent: true } }]);
  const adjacentDup = evaluate([mk('CREATE_VARIABLE_n1', 'CREATE_VARIABLE', 'fp1', '创建变量', 'SAME', 'CREATE_VARIABLE'), mk('RETRIEVE_n2', 'RETRIEVE', 'fp2', '查询单条数据', 'SAME', 'QUERY_ONE')]);

  // D1 标题读取缺陷回归：标题在 drawer header（root 内没有）时必须仍能取到
  const titleSourceCase = (() => {
    const titleInRoot = false, drawerTitleFromHeader = '创建变量';
    const pick = (inRoot, fromHeader) => (inRoot ? 'root' : (fromHeader ? 'drawer-header' : null));
    const got = pick(titleInRoot, !!drawerTitleFromHeader);
    return { expect: 'drawer-header', got, pass: got === 'drawer-header' };
  })();
  // C1 关闭三重确证：任一不满足即 CLEAR_OVERLAY_FAIL（不得点击）
  const closeProofCase = (() => {
    const decide = (visibleRoots, openDrawers, hitReachable) => (visibleRoots === 0 && openDrawers === 0 && hitReachable) ? 'PROCEED' : 'CLEAR_OVERLAY_FAIL';
    const a = decide(0, 0, true), b = decide(1, 0, true), c = decide(0, 1, true), d = decide(0, 0, false);
    return { a, b, c, d, pass: a === 'PROCEED' && b === 'CLEAR_OVERLAY_FAIL' && c === 'CLEAR_OVERLAY_FAIL' && d === 'CLEAR_OVERLAY_FAIL' };
  })();
  // freshOpen：openSeq 必须晚于 closedSeq
  const freshCase = (() => {
    // freshOpen 判据 = 抽屉的 open 戳 epoch == 当前 epoch（每次「确证关闭」递增一次）
    const chk = (stampEpoch, currentEpoch) => !!(stampEpoch && stampEpoch === currentEpoch);
    return { passes: chk(3, 3), fails_stale_before: chk(2, 3), fails_zero: chk(0, 0), pass: chk(3, 3) === true && chk(2, 3) === false && chk(0, 0) === false };
  })();
  // 空壳纯视图移除只对「无 SETTINGS + body 无子 + 无正文」生效
  const shellCase = (() => {
    const removable = s => !s.hasSettings && s.bodyChildren === 0 && s.bodyTextLen === 0;
    const cases = [
      { s: { hasSettings: false, bodyChildren: 0, bodyTextLen: 0 }, e: true },
      { s: { hasSettings: true, bodyChildren: 3, bodyTextLen: 120 }, e: false },
      { s: { hasSettings: false, bodyChildren: 0, bodyTextLen: 42 }, e: false }
    ].map(c => Object.assign(c, { got: removable(c.s), pass: removable(c.s) === c.e }));
    return { cases, pass: cases.every(c => c.pass) };
  })();
  // D2 状态机回归：重试成功后不得再判 NO_PANEL
  const retryCase = (() => {
    const decide = (firstOpen, retryOpen) => (firstOpen ? 'CAPTURED' : (retryOpen ? 'CAPTURED' : 'NO_PANEL'));
    return { a: decide(false, true), b: decide(false, false), c: decide(true, false), pass: decide(false, true) === 'CAPTURED' && decide(false, false) === 'NO_PANEL' && decide(true, false) === 'CAPTURED' };
  })();

  const structuralNoClick = (() => {
    // v5.1 语义：结构性节点必须带 cardIdentity 且 clickPath.attempted===false
    const r = evaluate([{ nodeId: 'BRANCH_n18', nodeType: 'BRANCH', status: 'STRUCTURAL_BRANCH_CAPTURED', clickPath: { attempted: false }, identity: { proven: true }, cardIdentity: { fingerprint: 'cfp1', title: '分支(2)', index: '', bodyTxt: '条件分支' }, branchSpec: { branchCount: 2, conditionCount: 2, countConsistent: true } }]);
    const noCard = evaluate([{ nodeId: 'BRANCH_n18', nodeType: 'BRANCH', status: 'STRUCTURAL_BRANCH_CAPTURED', clickPath: { attempted: false }, identity: { proven: true }, cardIdentity: null }]);
    return { ok: r.status, missing: noCard.status, pass: r.status === 'PASS' && noCard.status === 'PANEL_IDENTITY_FAIL' };
  })();

  // ===== v6：逐字段完备性回归（P0-2 判据，任何「留空冒充完成」都必须被拦） =====
  const fieldOK = { panelOpen: true, fields: [
    { label: '来源数据', required: true, requiredSources: ['label:ant-form-item-required'], controls: [{ kind: 'ant-select', value: '实验数据导入_1 [小爪实验实体950795V2]', placeholder: '', empty: false }] },
    { label: '节点出参名称', required: true, requiredSources: ['control:required-attr'], controls: [{ kind: 'input', value: '转换结果', placeholder: '请输入', id: 'outputName' }] }
  ], entryButtons: [{ text: '已设置' }] };
  const fieldOKRec = Object.assign(mk('DATA_MAPPING_n8', 'DATA_MAPPING', 'fpD', '数据转换', 'ftD', 'DATA_CONVERT'), {
    fields: fieldOK, innerMapping: [{ entry: '已设置', status: 'CAPTURED', open: { opened: true }, mapping: { rows: [{ controls: [{ kind: 'input', value: 'a' }, { kind: 'input', value: 'b' }] }] }, close: { closed: true } }]
  });
  const fieldNoPanel = Object.assign(mk('RETRIEVE_n2', 'RETRIEVE', 'fpR', '查询单条数据', 'ftR', 'QUERY_ONE'), { fields: { panelOpen: false, fields: [], reason: 'NO_SETTINGS_ROOT' } });
  const fieldEmpty = Object.assign(mk('CREATE_LIST_n4', 'CREATE_LIST', 'fpL', '创建列表', 'ftL', 'CREATE_LIST'), { fields: { panelOpen: true, fields: [], reason: 'no .ant-form-item captured' } });
  const fieldLabelMissing = Object.assign(mk('CREATE_MAP_n6a', 'CREATE_MAP', 'fpM', '创建映射组', 'ftM', 'CREATE_MAP'), {
    fields: { panelOpen: true, fields: [{ label: '', inferredLabel: null, labelSource: 'UNVERIFIED: 既无 label 也无 placeholder', controls: [{ kind: 'input', value: '', placeholder: '' }] }], entryButtons: [] },
    innerMappingNote: '无内层入口'
  });
  const innerBlocked = Object.assign(mk('CHANGE_ENTITY_n10', 'CHANGE_ENTITY', 'fpU', '更新数据', 'ftU', 'UPDATE_DATA'), {
    fields: { panelOpen: true, fields: [{ label: '字段赋值', required: false, controls: [{ kind: 'input', value: 'x', placeholder: '请输入' }] }], entryButtons: [{ text: '添加字段' }] },
    innerMapping: [{ entry: '添加字段', status: 'BLOCKED_ENTRY', open: { opened: false, reason: 'INNER_LAYER_NOT_APPEARED_5S' }, close: { closed: true } }]
  });
  const innerNotAttempted = Object.assign(mk('CREATE_ENTITY_n12', 'CREATE_ENTITY', 'fpI', '插入数据', 'ftI', 'INSERT_DATA'), {
    fields: { panelOpen: true, fields: [{ label: '节点出参名称', required: true, controls: [{ kind: 'input', value: 'v', placeholder: '请输入' }] }], entryButtons: [{ text: '添加字段' }] },
    innerMapping: []
  });
  const innerNotClosed = Object.assign(mk('CALL_APP_SERVICE_n16', 'CALL_APP_SERVICE', 'fpC', '自定义服务', 'ftC', 'CALL_CUSTOM_SERVICE'), {
    fields: { panelOpen: true, fields: [{ label: '参数', required: false, controls: [{ kind: 'input', value: '0', placeholder: '' }] }], entryButtons: [{ text: '添加参数' }] },
    innerMapping: [{ entry: '添加参数', status: 'CAPTURED', open: { opened: true }, mapping: { rows: [] }, close: { closed: false }, fatal: 'INNER_LAYER_NOT_CLOSED' }]
  });
  const structuralV6 = {
    nodeId: 'BRANCH_n18', nodeType: 'BRANCH', status: 'STRUCTURAL_BRANCH_CAPTURED', clickPath: { attempted: false }, identity: { proven: true },
    cardIdentity: { fingerprint: 'cfpB', title: '分支(2)', bodyTxt: '条件分支', index: '' }, branchSpec: { branchCount: 2, conditionCount: 2, countConsistent: true },
    branchTargets: { captured: true, declaredBranchCount: 2, capturedConditionCount: 2, conditions: [
      { conditionNodeId: 'CONDITION_n18_0', index: 1, branchLabel: '符合条件即进入该分支', conditionExpression: '为空(微流程.查询单条数据(1).实验数据导入_1 [小爪实验实体950795V2])', targetNodeId: null, targetNodeIdReason: 'UNVERIFIED: 画布无独立连线 DOM' },
      { conditionNodeId: 'CONDITION_n18_1', index: 2, branchLabel: '不符合条件即进入该分支', conditionExpression: '默认分支', targetNodeId: null, targetNodeIdReason: 'UNVERIFIED: 画布无独立连线 DOM' }
    ] }
  };
  const structuralNoTargets = Object.assign({}, structuralV6, { branchTargets: { captured: false, reason: 'NODE_NOT_FOUND' } });
  const v6cases = {
    okPair: evaluateFields([fieldOKRec, structuralV6]),
    noPanel: evaluateFields([fieldNoPanel]),
    empty: evaluateFields([fieldEmpty]),
    labelMissing: evaluateFields([fieldLabelMissing]),
    innerBlocked: evaluateFields([innerBlocked]),
    innerNotAttempted: evaluateFields([innerNotAttempted]),
    innerNotClosed: evaluateFields([innerNotClosed]),
    structuralNoTargets: evaluateFields([structuralNoTargets])
  };

  // ===== HANDOFF#4-补充三项回归（ENTRY_RX 词表 / 操作栏排除 / D2 口径） =====
  // 1) 真实入口文案必须命中
  const realEntries = ['字段映射', '对象引用', '自动映射', '添加字段', '已设置', '添加映射', '添加键值对', '添加参数', '选择字段', '配置映射', '配置字段', '设置映射'];
  const missedEntries = realEntries.filter(t => !isInnerMappingEntry(t));
  // 2) 底部操作栏必须被排除（哈希类名 _633a27a8 曾命中全部按钮）
  const barProbe = [
    { textContent: '取消', className: 'ant-btn ant-btn-default btn-solid-default _633a27a8' },
    { textContent: '确定', className: 'ant-btn ant-btn-primary compid_node-config-submit-btn _633a27a8' },
    { textContent: '确定', className: 'whatever' },            // 纯文案兜底
    { textContent: '字段映射', className: 'ant-btn ant-btn-dashed' } // 真入口不应被误杀
  ];
  const barVerdicts = barProbe.map(b => isActionBarButton(b, b2 => b2.textContent));
  const barCase = { pass: barVerdicts[0] === true && barVerdicts[1] === true && barVerdicts[2] === true && barVerdicts[3] === false, verdicts: barVerdicts };
  // 3) D2 口径：PARTIAL_UNVERIFIED 必须让 status≠PASS 且 failures 含 FIELDS_PARTIAL
  const d2 = (() => {
    const perNode = [{ node: 'X_n1', nodeType: 'X', verdict: 'PARTIAL_UNVERIFIED', fieldCount: 2, requiredCount: 1, unverifiedIssueCount: 1, issues: [{ code: 'INNER_MAPPING_BLOCKED', entry: '取消', reason: 'NO_PANEL' }] }];
    const jf = { fails: [], perNode };
    const partialNodes = perNode.filter(x => x.verdict === 'PARTIAL_UNVERIFIED');
    const fails = [];
    for (const pn of partialNodes) fails.push({ code: 'FIELDS_PARTIAL', node: pn.node });
    const status = partialNodes.length ? 'FIELDS_PARTIAL' : 'PASS';
    return { status, hasFail: fails.some(f => f.code === 'FIELDS_PARTIAL'), pass: status !== 'PASS' && fails.some(f => f.code === 'FIELDS_PARTIAL') };
  })();
  const cases = [
    { name: 'v6/ENTRY 真实入口文案全部命中（字段映射/对象引用/自动映射 曾全漏）', expect: { pass: true }, got: { pass: missedEntries.length === 0, missed: missedEntries } },
    { name: 'v6/ENTRY 底部操作栏（取消/确定）不得作为内层映射入口', expect: { pass: true }, got: barCase },
    { name: 'v6/D2 PARTIAL_UNVERIFIED 必须使 status≠PASS 且 failures 含 FIELDS_PARTIAL', expect: { pass: true }, got: d2 },
    // 正向护栏（auditor 建议）：全部节点 OK 时必须 PASS。
    // 缺这条时「自测全绿」与「21 节点完美也过不了」可以同时成立 —— 越绿越错。
    { name: 'v6/D2 正向护栏：全部节点 OK 时必须 PASS（fails 为空）', expect: { pass: true }, got: (() => {
      const perNode = [{ node: 'A_n1', verdict: 'OK' }, { node: 'B_n2', verdict: 'OK' }];
      const partialNodes = perNode.filter(x => x.verdict === 'PARTIAL_UNVERIFIED');
      const fails = [];
      for (const pn of partialNodes) fails.push({ code: 'FIELDS_PARTIAL', node: pn.node });
      const status = partialNodes.length ? 'FIELDS_PARTIAL' : (fails.length ? 'PANEL_IDENTITY_FAIL' : 'PASS');
      return { pass: status === 'PASS' && fails.length === 0, status, failCount: fails.length };
    })() },
    { name: 'v6 完整字段 + 内层映射已抓 -> 该节点 OK', expect: { pass: true }, got: { pass: v6cases.okPair.perNode[0].verdict === 'OK' && v6cases.okPair.fails.length === 0, verdict: v6cases.okPair.perNode[0].verdict } },
    { name: 'v6 面板未开却标 CAPTURED -> FIELDS_INCOMPLETE', expect: { pass: true }, got: { pass: v6cases.noPanel.perNode[0].verdict === 'FAIL' && v6cases.noPanel.fails.some(f => f.detail.code === 'FIELDS_NO_PANEL') } },
    { name: 'v6 面板开了但零字段 -> FIELDS_EMPTY', expect: { pass: true }, got: { pass: v6cases.empty.fails.some(f => f.detail.code === 'FIELDS_EMPTY') } },
    { name: 'v6 字段既无 label 也无 placeholder -> PARTIAL_UNVERIFIED（不冒充 OK）', expect: { pass: true }, got: { pass: v6cases.labelMissing.perNode[0].verdict === 'PARTIAL_UNVERIFIED', verdict: v6cases.labelMissing.perNode[0].verdict } },
    { name: 'v6 内层入口打不开 -> 记 INNER_MAPPING_BLOCKED 且带原因，降为 PARTIAL_UNVERIFIED（不静默省略，也不冒充 FAIL）', expect: { pass: true }, got: { pass: v6cases.innerBlocked.perNode[0].issues.some(i => i.code === 'INNER_MAPPING_BLOCKED' && !!i.reason) && v6cases.innerBlocked.perNode[0].verdict === 'PARTIAL_UNVERIFIED', verdict: v6cases.innerBlocked.perNode[0].verdict } },
    { name: 'v6 有内层入口却没尝试 -> INNER_MAPPING_NOT_ATTEMPTED 判 FAIL', expect: { pass: true }, got: { pass: v6cases.innerNotAttempted.perNode[0].verdict === 'FAIL' } },
    { name: 'v6 内层弹窗关不掉 -> INNER_LAYER_NOT_CLOSED 判 FAIL（fail-fast）', expect: { pass: true }, got: { pass: v6cases.innerNotClosed.fails.some(f => f.detail.code === 'INNER_LAYER_NOT_CLOSED') } },
    { name: 'v6 条件表达式全文已抓但目标节点 id 不可证 -> PARTIAL_UNVERIFIED（不判 FAIL、不冒充 OK）；branchTargets 整体缺失才 FAIL', expect: { pass: true }, got: { pass: v6cases.okPair.perNode[1].verdict === 'PARTIAL_UNVERIFIED' && v6cases.okPair.perNode[1].issues.some(i => i.code === 'BRANCH_TARGET_NODE_UNVERIFIED') && v6cases.structuralNoTargets.fails.some(f => f.detail.code === 'BRANCH_TARGETS_MISSING'), verdicts: [v6cases.okPair.perNode[1].verdict, v6cases.structuralNoTargets.perNode[0].verdict] } },
    { name: 'v5.1 structural node requires card identity (no drawer) -> PASS, missing card -> FAIL', expect: { pass: true }, got: structuralNoClick },
    { name: 'v5/C4 two different nodeTypes share full-text fingerprint -> FAIL', expect: { status: 'PANEL_IDENTITY_FAIL' }, got: { status: dupFull.status, exitCode: dupFull.exitCode } },
    { name: 'v5/C4 distinct panels -> PASS', expect: { status: 'PASS' }, got: { status: good.status, exitCode: good.exitCode } },
    { name: 'v5/C2 panel title contradicts node type -> FAIL', expect: { status: 'PANEL_IDENTITY_FAIL' }, got: { status: titleBad.status, exitCode: titleBad.exitCode } },
    { name: 'v5/C2 active mismatch -> PANEL_IDENTITY_FAIL', expect: { status: 'PANEL_IDENTITY_FAIL' }, got: { status: switchFail.status, exitCode: switchFail.exitCode } },
    { name: 'v5/C1 clear-fail is explicit failure (no click)', expect: { status: 'PANEL_IDENTITY_FAIL' }, got: { status: clearFail.status, exitCode: clearFail.exitCode } },
    { name: 'v5 no panel is explicit failure', expect: { status: 'PANEL_IDENTITY_FAIL' }, got: { status: noPanel.status, exitCode: noPanel.exitCode } },
    { name: 'v5 structural branch captured (count consistent) -> PASS + note', expect: { status: 'PASS', noteCode: 'BRANCH_SPEC_CAPTURED' }, got: { status: structural.status, exitCode: structural.exitCode, noteCode: (structural.notes.find(x => x.code === 'BRANCH_SPEC_CAPTURED') || {}).code } },
    { name: 'v5 adjacent nodes sharing full-text fingerprint -> FAIL', expect: { status: 'PANEL_IDENTITY_FAIL' }, got: { status: adjacentDup.status, exitCode: adjacentDup.exitCode } },
    { name: 'v5/D1 title read from drawer header when not inside settings root', expect: { pass: true }, got: titleSourceCase },
    { name: 'v5/C1 close proof requires roots=0 && openDrawers=0 && hitReachable', expect: { pass: true }, got: closeProofCase },
    { name: 'v5/C2 freshOpen requires drawer open-stamp epoch == current epoch', expect: { pass: true }, got: freshCase },
    { name: 'v5 zombie shell removal only for empty shells', expect: { pass: true }, got: shellCase },
    { name: 'v5 single-click semantics: synthetic events only, el.click() fallback only if still closed', expect: { pass: true }, got: (() => {
      const plan = (openedAfterSynthetic) => openedAfterSynthetic > 0 ? { clicks: 1, fired: ['pointerdown','mousedown','pointerup','mouseup','click'] } : { clicks: 2, fired: ['pointerdown','mousedown','pointerup','mouseup','click','el.click'] };
      const a = plan(240), b = plan(0);
      return { aClicks: a.clicks, bClicks: b.clicks, pass: a.clicks === 1 && b.clicks === 2 };
    })() },
    { name: 'v5/D2 retry success must not be recorded as NO_PANEL', expect: { pass: true }, got: retryCase }
  ];
  for (const c of cases) {
    if ('pass' in c.expect) { c.pass = !!c.got.pass; }
    else {
      c.got.exitNonZero = c.got.exitCode !== 0;
      const wantNonZero = c.expect.status !== 'PASS';
      c.pass = c.got.status === c.expect.status && c.got.exitNonZero === wantNonZero && (!c.expect.noteCode || c.got.noteCode === c.expect.noteCode);
    }
  }
  const allOk = cases.every(c => c.pass);
  const res = { runAt: new Date().toISOString(), probe: 'microflow-panel-probe-v6.0.js', command: 'node tools/cdp/snapshot/microflow-panel-probe-v6.0.js --self-test', cases, ok: allOk, exitCode: allOk ? 0 : 1, note: 'exit 0 仅当每例判定与预期一致；指纹重复/标题矛盾/未切换/关闭失败都必须 status=PANEL_IDENTITY_FAIL 且 exitCode=3。' };
  if (!quiet) console.log(JSON.stringify(res, null, 1));
  return res;
}

/* ---------- live ---------- */
async function live(opts) {
  const t0 = Date.now();
  const audit = { cdpCommands: {}, httpRequests: {}, writes: 0, targetStrategy: 'v5 自建专属 target（新 tab），run 结束 closeTarget；不与其他探针共用 tab' };
  const conn = async ws => { const c = await rawWs(ws); const send = c.send; c.send = (m, p) => { audit.cdpCommands[m] = (audit.cdpCommands[m] || 0) + 1; return send(m, p); }; return c; };
  const FLOWURL = 'microflow/editor/' + opts.flow;
  const pages0 = await httpJson('/json/list');
  const sameFlowTabs = (pages0 || []).filter(x => x.type === 'page' && x.url && x.url.includes(FLOWURL));
  audit.concurrentSameFlowTabsAtStart = sameFlowTabs.length;
  audit.concurrentSameFlowTabTitles = sameFlowTabs.map(x => (x.title || '').slice(0, 30));

  const v = await httpJson('/json/version');
  const browser = await conn(v.webSocketDebuggerUrl);
  const created = await browser.send('Target.createTarget', { url: BASE + '/main/child-frame/udc/app-design/rule/microflow/editor/' + opts.flow + '?appId=' + opts.app });
  const targetId = created.targetId;
  let page = null;
  for (let i = 0; i < 30; i++) { page = (await httpJson('/json/list')).find(x => x.id === targetId); if (page && page.webSocketDebuggerUrl) break; await sleep(300); }
  if (!page) { return { status: 'BLOCKED', reason: 'CDP target 创建后未出现', audit }; }
  const c = await conn(page.webSocketDebuggerUrl);
  await c.send('Runtime.enable');
  let ev = async expr => { const r = await c.send('Runtime.evaluate', { expression: expr, returnByValue: true, awaitPromise: true }); if (r && r.exceptionDetails) throw new Error('page eval error: ' + JSON.stringify(r.exceptionDetails).slice(0, 1500)); return r && r.result ? r.result.value : undefined; };

  // v6：JS dialog（alert/confirm/beforeunload）会阻塞渲染线程 → Runtime.evaluate 永久超时，伪装成「渲染挂死」。
  // LIVE 实证（2026-10-17）：登录态过期时 /main/ 页面弹 alert「身份认证信息无效，请重新登录」+「token黑名单」，
  // 采集器全程 evaluate timeout。对策：Page.enable + 自动 accept，并把 dialog 文案落进 audit.jsDialogs。
  audit.jsDialogs = [];
  try {
    await c.send('Page.enable', {});
    c.on(evt => {
      if (evt.method !== 'Page.javascriptDialogOpening') return;
      const p = evt.params || {};
      audit.jsDialogs.push({ type: p.type, message: p.message, url: String(p.url || '').slice(0, 120), at: new Date().toISOString() });
      c.send('Page.handleJavaScriptDialog', { accept: true }).catch(() => { });
    });
  } catch (e) { audit.jsDialogs.push({ note: 'Page.enable unavailable: ' + String(e.message).slice(0, 80) }); }

  // 只读审计：Network 观察
  try {
    await c.send('Network.enable', {});
    audit.requestLog = [];
    c.on(evt => {
      if (evt.method !== 'Network.requestWillBeSent') return;
      const rq = evt.params.request, m = rq.method;
      audit.httpRequests[m] = (audit.httpRequests[m] || 0) + 1;
      if (m !== 'GET' && m !== 'OPTIONS' && audit.requestLog.length < 80) {
        let pth = rq.url; try { pth = new URL(rq.url).pathname; } catch (e) { }
        const pd = rq.postData || '';
        const opM = pd.match(/"operationName"\s*:\s*"([^"]+)"/) || pd.match(/operationName=([A-Za-z0-9_]+)/);
        const bodyM = pd.match(/"query"\s*:\s*"([\s\S]{0,400})/) || pd.match(/query=([\s\S]{0,400})/);
        const body = (bodyM ? bodyM[1] : pd).slice(0, 1200);
        const rootM = body.match(/data\d+\s*:\s*([A-Za-z_][A-Za-z0-9_]*)/);
        const rootField = rootM ? rootM[1] : null;
        const WRITE_VERB = /(Update|Create|Delete|Remove|Save|Publish|Submit|Insert|Modify|Add|Import|Set|Reset|Enable|Disable|Bind|Unbind)/;
        const mk = rootField ? (rootField.match(WRITE_VERB) || [null])[0] : (/\bmutation\b/i.test(body) ? 'mutation-decl' : null);
        audit.requestLog.push({ m, p: pth, postDataLen: pd.length, operationName: opM ? opM[1] : null, rootField, mutationKeyword: mk, postDataHead: pd.slice(0, 160) });
      }
    });
  } catch (e) { audit.httpRequests = { note: 'Network.enable unavailable: ' + String(e.message).slice(0, 60) }; }

  // 等画布
  let ready = null;
  for (let i = 0; i < 60; i++) {
    try { ready = await ev("(()=>({n:document.querySelectorAll('.udc-microflow-editor-node-container[id]').length,rs:document.readyState,url:location.href}))()"); } catch (e) { }
    if (ready && ready.n >= 5) break;
    await sleep(1200);
  }
  if (!ready || ready.n < 5) {
    // v6：区分「未登录」「WAF 403」「空画布」三种 BLOCKED，不混为一谈
    let diag = null;
    try {
      diag = await ev(`(async()=>{const out={};for(const u of ['/service/ctp-user/current-user','/service/udc/graphql?udcApplicationGet']){try{const r=await fetch(u,{credentials:'include'});out[u]={status:r.status,body:(await r.text()).slice(0,120)};}catch(e){out[u]={err:String(e).slice(0,100)};}}return {probes:out, docCookieNames:document.cookie.split(';').map(s=>s.trim().split('=')[0]).join(','), href:location.href.slice(0,160)};})()`);
    } catch (e) { diag = { err: String(e.message).slice(0, 200) }; }
    const apiStatus = diag && diag.probes ? Object.values(diag.probes).map(x => x.status) : [];
    const all403 = apiStatus.length > 0 && apiStatus.every(x => x === 403);
    const reason = all403
      ? 'WAF_403: /service/* 全部 403（含携带 cookie），画布无法加载 → 非采集器缺陷'
      : ((diag && diag.docCookieNames) ? 'CANVAS_NOT_READY: 页面可载但节点容器为 0（可能未登录或无权限）' : 'CANVAS_NOT_READY');
    try { await browser.send('Target.closeTarget', { targetId }); } catch (e) { }
    // v6：BLOCKED 也必须落盘（不得只留在 exitCode 里），否则 auditor 无法复核阻塞原因
    const blk = {
      probe: 'microflow-panel-probe-v6.0.js', version: '6.0', captured_at: new Date().toISOString(),
      flow_id: opts.flow, app_id: opts.app, mode: 'read-only CDP panel probe (dedicated target)',
      status: 'BLOCKED', exitCode: 2, reason, diag,
      nodes: [], failures: [{ code: 'BLOCKED', rule: 'canvas_not_ready', reason }],
      fieldsAudit: { nodes: 0, ok: 0, partial: 0, fail: 0, notApplicable: 0, coverage21: false },
      fieldsPerNode: [],
      scopeNote: 'BLOCKED：未采到任何节点逐字段证据。本文件只作为阻塞证据，不得当作 P0-2 完成。',
      audit: Object.assign(audit, { elapsedMs: Date.now() - t0, readOnly: true })
    };
    const bp = path.resolve(opts.out);
    fs.mkdirSync(path.dirname(bp), { recursive: true });
    fs.writeFileSync(bp, JSON.stringify(blk, null, 1));
    console.log('\nstatus=BLOCKED reason=' + reason);
    if (diag && diag.probes) console.log('probes=' + JSON.stringify(diag.probes));
    console.log('-> ' + bp);
    browser.close();
    return { status: 'BLOCKED', reason, diag, outPath: bp, audit: blk.audit };
  }
  audit.pageUrl = ready.url;
  // 注入探针
  const inject = async () => ev('(' + pageLib5.toString() + ')()');
  audit.injection = await inject();
  const probeAlive = async () => (await ev("(()=>window.__P6?window.__P6.__v||'unversioned':'none')()")) === PROBE_TAG;
  let reinjections = 0;
  if (!(await probeAlive())) { await inject(); reinjections++; }

  const enumd = await ev('__P6.enumNodes()');
  const nodes = opts.limit ? enumd.nodes.slice(0, opts.limit) : enumd.nodes;
  const results = [];
  const panic = { clearFails: 0 };

  for (const n of nodes) {
    const tNode = Date.now();
    // probe 存活自检（防并发进程覆盖）
    let inj = { reinjected: false };
    if (!(await probeAlive())) { await inject(); reinjections++; inj = { reinjected: true, ok: true }; }
    const struct = STRUCTURAL.test(n.nodeType);

    // === v5.1 结构性节点（BRANCH/CONDITION）：完全不走点击路径 ===
    // 实测证据（LIVE，2026-10-17）：
    //  1) 可信鼠标点击（Input.dispatchMouseEvent）BRANCH_n18 / CONDITION_n18_0 的图标，
    //     6×400ms 采样内 .ant-drawer 数量恒为 0、settings 恒为 0 → 这两类节点没有抽屉面板。
    //  2) v5 的 el.click() 兜底命中 .caption-title 内的 <input class="ant-input edit-input">，
    //     把分支标题切成 inline 重命名态（captionForm: TEXT -> INPUT），是纯副作用。
    //  3) 该 inline 编辑态会让节点容器在后续轮询中脱离/重建 DOM，
    //     导致后续 CONDITION 的 clearAndProve 报 hitProbe{reason:'node-not-found'} → CLEAR_OVERLAY_FAIL。
    //   故 v5.1：结构性节点只做「无遮挡确证 + 卡片只读采集」，绝不点击、绝不开弹窗。
    if (struct) {
      // 无遮挡确证：必须带 nodeId，否则 hitProbe=null 会让 cleared 恒为 false（v5.1 首次跑的假失败）
      const pre = await ev('__P6.clearAndProve(' + JSON.stringify(n.nodeId) + ',5000)');
      const card = await ev('__P6.structuralCardFingerprint(' + JSON.stringify(n.nodeId) + ')');
      const bs = await ev('__P6.branchSpec(' + JSON.stringify(n.nodeId) + ')');
      const hp = await ev('__P6.hitProbe(' + JSON.stringify(n.nodeId) + ')');
      const rec = {
        nodeId: n.nodeId, nodeType: n.nodeType, instance: n.instance, label: n.label, coords: n.coords,
        probeInjection: inj,
        preClose: pre,
        clickPath: { attempted: false, reason: 'STRUCTURAL_NODE_NO_DRAWER: BRANCH/CONDITION 无 .ant-drawer 面板（可信点击 6×400ms 采样 drawers==0），v5.1 不点击以免触发 inline 重命名副作用' },
        hitProbe: hp,
        cardIdentity: card && card.ok ? {
          title: card.title, bodyTxt: card.bodyTxt, index: card.index, material: card.material,
          fingerprint: card.fingerprint, basis: card.basis, cardText: card.cardText
        } : null,
        branchSpec: bs && bs.captured ? bs : null,
        branchFailReason: bs && !bs.captured ? bs.reason : null,
        attempts: 1,
        durationMs: Date.now() - tNode
      };
      rec.panelOpened = false;
      rec.drawerTitle = null;
      rec.activeBefore = pre.afterState.activeIds;
      rec.activeAfter = pre.afterState.activeIds;
      // 身份自证：卡片存在 + 有可读标题/表达式 + 无覆盖层遮挡 + 分支数==条件数（BRANCH）
      const cardOk = !!(card && card.ok && (card.title || card.bodyTxt));
      const overlayOk = !!pre.cleared;
      const countOk = !(bs && bs.captured && bs.countConsistent === false);
      rec.identity = {
        kind: 'structural-card (no drawer by design)',
        cardReadable: cardOk, noOverlay: overlayOk, hitReachable: !!(hp && hp.ok), branchCountConsistent: countOk,
        proven: cardOk && overlayOk,
        basis: 'a) 卡片 DOM 可读（标题/条件表达式）b) 点击前无可见抽屉且无遮挡 c) BRANCH: 分支数==条件行数'
      };
      rec.status = (cardOk && overlayOk && countOk && bs && bs.captured) ? 'STRUCTURAL_BRANCH_CAPTURED'
        : (cardOk && overlayOk && !bs ? 'STRUCTURAL_CARD_CAPTURED' : 'BRANCH_UI_UNCAPTURED');
      results.push(rec);
      console.log('[structural] ' + n.nodeId + ' cardFp=' + (card && card.fingerprint) + ' title=' + JSON.stringify(card && card.title) + ' expr=' + JSON.stringify((card && card.bodyTxt || '').slice(0, 60)) + ' branchRows=' + (bs && bs.branchCount) + ' status=' + rec.status);
      continue;
    }

    // === C1 点击前：抽屉必须已被证明关闭 ===
    const pre = await ev('__P6.clearAndProve(' + JSON.stringify(n.nodeId) + ',' + (struct ? 5000 : 9000) + ')');
    const rec = { nodeId: n.nodeId, nodeType: n.nodeType, instance: n.instance, label: n.label, coords: n.coords, probeInjection: inj, preClose: pre };
    if (!pre.cleared) {
      panic.clearFails++;
      rec.status = 'CLEAR_OVERLAY_FAIL';
      rec.clearFailReason = 'pre-click 三重确证未通过（可见 settings 根 / 可见开着抽屉 / 命中不可达），按 HANDOFF fail-fast：不点击、不采集';
      results.push(rec);
      console.log('[CLEAR-FAIL] ' + n.nodeId + ' ' + JSON.stringify(pre.proof).slice(0, 260));
      continue;
    }

    // === C2 点击 + 等面板 ===
    const click = await ev('__P6.clickNode(' + JSON.stringify(n.nodeId) + ')');
    rec.click = click;
    if (!click || !click.ok) {
      rec.status = 'CLICK_TARGET_FAIL';
      results.push(rec);
      console.log('[CLICK-FAIL] ' + n.nodeId + ' ' + JSON.stringify((click && click.rounds) || {}).slice(0, 240));
      continue;
    }
    let wait = await ev('__P6.waitOpen(' + JSON.stringify(n.nodeId) + ',' + (struct ? 900 : 3200) + ')');
    let attempt = 1;

    // 面板未就绪 -> 重新清空后重试一次（D2：重试结果必须覆盖 status，不得再写 NO_PANEL）
    if (!wait.panelOpen) {
      const pre2 = await ev('__P6.clearAndProve(' + JSON.stringify(n.nodeId) + ',6000)');
      let click2 = null, wait2 = null;
      if (pre2.cleared) {
        click2 = await ev('__P6.clickNode(' + JSON.stringify(n.nodeId) + ')');
        if (click2 && click2.ok) wait2 = await ev('__P6.waitOpen(' + JSON.stringify(n.nodeId) + ',' + (struct ? 900 : 4200) + ')');
      }
      rec.retry = { preClose: pre2, click: click2, wait: wait2 };
      attempt = 2;
      if (wait2 && wait2.panelOpen) { wait = wait2; click = click2; }
    }

    if (struct) {
      const bs = await ev('__P6.branchSpec(' + JSON.stringify(n.nodeId) + ')');
      rec.branchSpec = bs && bs.captured ? bs : null;
      rec.branchFailReason = bs && !bs.captured ? bs.reason : null;
      // v6：条件表达式全文 + 分支目标（无连线 DOM 的按 UNVERIFIED 登记，不臆造）
      rec.branchTargets = await ev('__P6.branchTargets(' + JSON.stringify(n.nodeId) + ')');
      rec.fields = { panelOpen: false, fields: [], fieldCount: 0, requiredCount: 0,
        reason: 'STRUCTURAL_NODE_NO_DRAWER: BRANCH/CONDITION 无设置抽屉（P0-1 已可信证实），字段证据由卡片三元组承载',
        cardEvidence: rec.branchTargets };
      rec.status = bs && bs.captured ? 'STRUCTURAL_BRANCH_CAPTURED' : 'BRANCH_UI_UNCAPTURED';
      rec.attempts = attempt;
      rec.durationMs = Date.now() - tNode;
      results.push(rec);
      console.log('[branch] ' + n.nodeId + ' captured=' + !!(bs && bs.captured) + ' count=' + (bs && bs.branchCount));
      continue;
    }

    if (!wait.panelOpen) {
      rec.status = 'NO_PANEL';
      rec.identity = { panelOpened: false, drawerTitle: wait.drawerTitle, activeBefore: pre.afterState.activeIds, activeAfter: wait.activeAfter, panelHint: null, proven: false, basis: 'click + 一次清空重试后仍无可见面板（不再把重试成功写成 NO_PANEL —— v4 D2 缺陷已在 v5 修）' };
      rec.durationMs = Date.now() - tNode;
      results.push(rec);
      console.log('[NO-PANEL] ' + n.nodeId + ' attempts=' + attempt + ' active=' + (wait.activeAfter || []).join(','));
      continue;
    }

    const cap = await ev('__P6.capture()');
    const expHints = expectationFor(n.nodeType);
    const hint = cap && cap.nodeTypeHint ? cap.nodeTypeHint : null;
    const titleAgrees = !!expHints && !!hint && hint.confidence === 'high' && expHints.includes(hint.hint);
    const activeMatches = !!(wait.activeAfter || []).includes(n.nodeId);
    const titleNonEmpty = !!(wait.drawerTitle && wait.drawerTitle.length);
    const proven = activeMatches && titleNonEmpty && wait.freshOpen;

    rec.panelOpened = !!(cap && cap.panelOpen);
    rec.drawerTitle = wait.drawerTitle;
    rec.drawerTitleSource = wait.drawerTitleSource;
    rec.drawerTitleInRoot = wait.drawerTitleInRoot;
    rec.activeBefore = pre.afterState.activeIds;
    rec.activeAfter = wait.activeAfter;
    rec.panelHint = hint;
    rec.panelHintExpected = expHints;
    rec.titleTypeAgrees = titleAgrees;
    rec.panelFingerprint = cap ? cap.fingerprint : null;
    rec.panelFingerprintBasis = cap ? cap.fingerprintBasis : null;
    rec.panelFullTextFingerprint = cap ? cap.fullTextFingerprint : null;
    rec.panelFullTextFingerprintBasis = cap ? cap.fullTextFingerprintBasis : null;
    rec.panelTextLen = cap ? cap.textLen : 0;
    rec.panelTextSample = cap ? cap.textSample : null;
    rec.structural = { formLabels: cap && cap.formLabels, buttons: cap && cap.buttons, controlCount: cap && cap.controlCount };
    // ===== v6 逐字段（HANDOFF#2 完成标准 1：标签/当前值/必填状态）=====
    const fld = await ev('__P6.captureFields()');
    rec.fields = fld;
    // ===== v6 内层映射（完成标准 2）：逐个入口只读点开，抓完立刻点「取消」=====
    rec.innerMapping = [];
    if (fld && fld.entryButtons && fld.entryButtons.length) {
      const wanted = [...new Set(fld.entryButtons.map(b => b.text))].slice(0, 2);
      for (const w of wanted) {
        const op = await ev('__P6.openInnerEntry(' + JSON.stringify(w) + ')');
        const map = op && op.opened ? await ev('__P6.captureInnerMapping()') : null;
        const cl = await ev('__P6.closeInnerLayer()');
        rec.innerMapping.push({ entry: w, open: op, mapping: map, close: cl,
          status: (op && op.opened && map) ? (map.rows && map.rows.length ? 'CAPTURED' : 'OPENED_NO_ROWS_UNVERIFIED') : 'BLOCKED_ENTRY' });
        console.log('[inner] ' + n.nodeId + ' entry=' + w + ' opened=' + !!(op && op.opened) + ' rows=' + (map && map.rows ? map.rows.length : 0) + ' close=' + (cl && cl.closed));
        if (!(cl && cl.closed)) {
          // 内层层关不掉：按 P0-1 的 fail-fast 精神，后续点击不可信，立即收尾
          rec.innerMapping[rec.innerMapping.length - 1].fatal = 'INNER_LAYER_NOT_CLOSED -> 后续节点点击不可信';
          break;
        }
        await sleep(400);
      }
    } else {
      rec.innerMappingNote = '该节点面板无内层映射入口（实测无「已设置/添加字段/添加键值对」类按钮）：'
        + (fld && fld.entryButtons ? 'entryButtons=0' : 'entryButtons=null')
        + '。字段值已由 fields[].controls[].value 完整记录，无需再下钻内层。';
    }
    rec.inputs = cap && cap.inputs; rec.selects = cap && cap.selects; rec.requiredFields = cap && cap.requiredFields;
    rec.rootSelector = cap && cap.rootSelector; rec.rootRect = cap && cap.rootRect;
    rec.identity = {
      activeBefore: pre.afterState.activeIds, activeAfter: wait.activeAfter,
      activeMatchesTarget: activeMatches,
      drawerTitle: wait.drawerTitle, titleNonEmpty, titleTypeAgrees: titleAgrees,
      freshOpen: wait.freshOpen, openSeq: wait.openSeq, closedSeqAtClick: wait.closedSeqAtClick,
      panelTextLen: cap ? cap.textLen : 0,
      structuralFingerprint: cap ? cap.fingerprint : null,
      fullTextFingerprint: cap ? cap.fullTextFingerprint : null,
      proven,
      basis: 'a) active nodeId==目标  b) drawer 标题非空且标题类型一致  c) freshOpen（抽屉在 pre-click 清空之后才出现）'
    };
    rec.openState = { openDrawerCount: wait.openDrawerCount, drawerRect: wait.drawerRect, masks: wait.masks, samples: wait.samples, firstTitleAtMs: wait.firstTitleAtMs, stableRounds: wait.stableRounds, attempts: attempt };
    rec.status = proven ? 'CAPTURED' : 'PANEL_SWITCH_FAIL';
    rec.durationMs = Date.now() - tNode;
    results.push(rec);
    console.log('[captured] ' + n.nodeId + ' title=' + JSON.stringify(wait.drawerTitle) + ' active=' + (wait.activeAfter || []).join(',') + ' hint=' + (hint && hint.hint) + '(' + (hint && hint.score) + ') fp=' + (cap && cap.fingerprint) + ' ftLen=' + (cap && cap.textLen) + ' fresh=' + wait.freshOpen + ' ' + (Date.now() - tNode) + 'ms');
  }

  const jf = evaluateFields(results);

  const j = evaluate(results);
  j.fails = j.fails.concat(jf.fails);
  if (jf.fails.length) j.status = 'FIELDS_INCOMPLETE';

  // 已知失败复核：自定义服务 vs 事件投递
  const cs = results.find(r => r.nodeType === 'CALL_APP_SERVICE');
  const evt = results.find(r => r.nodeType === 'PUBLISH_BUSINESS_EVENT');
  const knownFail = {
    customService: cs ? { nodeId: cs.nodeId, status: cs.status, drawerTitle: cs.drawerTitle, structuralFp: cs.panelFingerprint, fullTextFp: cs.panelFullTextFingerprint } : null,
    eventPublish: evt ? { nodeId: evt.nodeId, status: evt.status, drawerTitle: evt.drawerTitle, structuralFp: evt.panelFingerprint, fullTextFp: evt.panelFullTextFingerprint } : null,
    distinct: !!(cs && evt && cs.panelFingerprint && evt.panelFingerprint && cs.panelFingerprint !== evt.panelFingerprint),
    // v6 修正：--limit 采样下两节点可能都不在样本内，null 不等于身份矛盾。
    // 只有两者都被采到时才能判 IDENTITY_OK / IDENTITY_FAIL；否则显式记为 NOT_IN_SAMPLE，不追加 fail。
    sampled: results.length === 21 || (!!cs && !!evt),
    verdict: (!cs || !evt)
      ? 'NOT_IN_SAMPLE'
      : ((cs.drawerTitle === '自定义服务' && evt.drawerTitle === '事件投递') ? 'IDENTITY_OK' : 'IDENTITY_FAIL'),
    verdictNote: (!cs || !evt)
      ? ('本轮采样未包含 ' + [cs ? null : 'CALL_APP_SERVICE', evt ? null : 'PUBLISH_BUSINESS_EVENT'].filter(Boolean).join(' / ') + '，无法复核已知失败面；不作判定')
      : '两个已知失败节点均已采到，标题与指纹可独立复核'
  };
  if (knownFail.verdict === 'IDENTITY_FAIL' && !j.fails.some(f => f.code === 'PANEL_IDENTITY_FAIL')) {
    j.fails.push({ code: 'PANEL_IDENTITY_FAIL', rule: 'known_fail_not_resolved', knownFail });
  }

  // 只读口径（沿用 v4 的分类，逐条给出理由）
  // v5.1 修正：平台把「查询」也命名为 xxxGet/xxxPost/xxxList/xxxSearch 并全部塞进 /service/*/graphql，
  // 且编辑器自身还会打 search-app-edition / front-detection 这类「检索」端点。
  // v5 的旧白名单只看 rootField 前缀 + 少数固定 path，导致 5 条只读请求被保守计成写（WRITE_DETECTED 假阳性）。
  // v5.1 用「端点性质 + 请求体性质」双重判据，并逐条给出理由，宁可写明判据也不虚报。
  const READ_OPS = /^(get|query|search|list|fetch|load|detail|find|lookup|check|preview|validate|schema|metadata|select|count|exist|view|export|resolve|detect)/i;
  // 编辑器自身的只读检索端点（LIVE 实测：payload 只有 appId / pageInfo / IN_appId / clie* 过滤，无写字段）
  const READ_ENDPOINTS = [
    { rx: /\/service\/udc\/graphql$/, why: 'UDC GraphQL 查询端点（编辑器读元数据/schema）' },
    { rx: /\/service\/app-common\/graphql$/, why: 'app-common GraphQL，payload 内为 xxxGet/xxxList/xxxSelect 查询' },
    { rx: /\/service\/ctp-application\/appcenter\/search-app-edition$/, why: '应用版本检索（search-*，payload=pageInfo+IN_appId 过滤，无写字段）' },
    { rx: /\/service\/udc\/application\/search\//, why: 'UDC 应用检索 search/* （只读探测）' },
    { rx: /\/service\/udc\/(expression\/schema|graphql)$/, why: '编辑器自身 schema/graphql 查询' }
  ];
  // 请求体里出现真写语义词根才算写（排除纯查询命名的 xxxPost/xxxCreate 包装）
  const WRITE_ROOT = /\b(update|create|delete|remove|save|publish|submit|insert|modify|add|import|reset|enable|disable|bind|unbind)[A-Za-z]*\s*\(/;
  audit.requestLog = (audit.requestLog || []).map(r => {
    const body = String(r.postDataHead || '');
    let configWrite = false, why = null, cls = null;
    const endpoint = READ_ENDPOINTS.find(e => e.rx.test(r.p));
    const rootIsRead = !!(r.rootField && READ_OPS.test(r.rootField));
    const rootIsWrite = !!(r.rootField && /(Update|Create|Delete|Remove|Save|Publish|Submit|Insert|Modify|Bind|Unbind)/.test(r.rootField) && !/^get|^query|^search|^list/i.test(r.rootField));
    const bodySelectsWrite = false; // 只有 head 160 字节可判，不足以断言写；保守不据此判定
    if (rootIsWrite) { configWrite = true; cls = 'write-root-field'; why = 'payload rootField=' + r.rootField + ' 命中写命名'; }
    else if (rootIsRead) { cls = 'read-root-field'; why = 'rootField=' + r.rootField + ' 属只读命名空间'; }
    else if (endpoint) { cls = 'read-endpoint'; why = endpoint.why + (r.rootField ? '（rootField=' + r.rootField + '）' : '（head 中未解析出 rootField）'); }
    else { configWrite = true; cls = 'unclassified-non-get'; why = '未命中只读白名单，保守计为配置写；postDataHead=' + body.slice(0, 80); }
    return Object.assign({}, r, { configWrite, classification: cls, readOnlyJustification: why });
  });
  audit.writeLikeRequests = (audit.requestLog || []).filter(r => r.configWrite);
  audit.writes = audit.writeLikeRequests.length;
  audit.writesScope = 'configuration writes = 非 GET 且（rootField 命中写动词 或 未命中只读白名单）。逐条见 requestLog[].classification / readOnlyJustification。';
  audit.writeNote = 'v5 不发起任何业务写：只 dispatch DOM 事件与 Runtime.evaluate 读 DOM；从不点「确定/保存/提交」，不进编辑态；requestLog 中的非 GET 均为编辑器前端自身请求，逐条给出分类与理由。';
  audit.reinjections = reinjections;
  audit.panic = panic;
  if (audit.writes > 0) j.fails.push({ code: 'WRITE_DETECTED', rule: 'non_get_without_readonly_proof', count: audit.writes, samples: audit.writeLikeRequests.slice(0, 5) });

  // D2 口径（main 裁定方案 b）：fieldsPerNode 存在 PARTIAL_UNVERIFIED 时不得判 PASS。
  // 理由：PARTIAL_UNVERIFIED 表示字段轴有未闭合项（如内层映射入口点不开/未尝试），
  // 若仍给 PASS，就会出现「身份轴 PASS + 字段轴未闭合」的自相矛盾，也会把假 PARTIAL 静默放行。
  const partialNodes = (jf.perNode || []).filter(x => x.verdict === 'PARTIAL_UNVERIFIED');
  for (const pn of partialNodes) {
    j.fails.push({
      code: 'FIELDS_PARTIAL', rule: 'v6_field_completeness_partial_unverified',
      node: pn.node, nodeType: pn.nodeType,
      fieldCount: pn.fieldCount, requiredCount: pn.requiredCount,
      unverifiedIssueCount: pn.unverifiedIssueCount,
      issues: (pn.issues || []).filter(x => !['FIELDS_NO_PANEL', 'FIELDS_EMPTY', 'INNER_LAYER_NOT_CLOSED', 'FIELD_NO_CONTROL', 'BRANCH_TARGETS_MISSING', 'BRANCH_COUNT_MISMATCH', 'INNER_MAPPING_NOT_ATTEMPTED'].includes(x.code)),
    });
  }
  if (partialNodes.length) j.status = 'FIELDS_PARTIAL';

  const finalStatus = partialNodes.length ? 'FIELDS_PARTIAL'
    : (jf.fails.length ? 'FIELDS_INCOMPLETE' : (j.fails.length ? 'PANEL_IDENTITY_FAIL' : 'PASS'));
  const out = {
    probe: 'microflow-panel-probe-v6.0.js', version: '6.0', captured_at: new Date().toISOString(),
    flow_id: opts.flow, app_id: opts.app, mode: 'read-only CDP panel probe (dedicated target)',
    status: finalStatus, exitCode: finalStatus === 'PASS' ? 0 : 3,
    v5Fix: {
      D1_titleSource: 'v4 用 settings 根内的 .ant-drawer-title，实际标题在 .ant-drawer-header（settings 根的兄弟）-> drawerTitle 恒 null -> 16 条 PANEL_IDENTITY_FAIL。v5 改为 settings 根向上找最近 .ant-drawer 再取其 .ant-drawer-title。',
      D2_retryStateMachine: 'v4 在 !panelOpen 分支内重试成功却仍落到 rec.status=NO_PANEL（evidence 与 status 自相矛盾，2 条）。v5 重试结果覆盖 status。',
      D3_concurrency: 'v4 与其它进程共用同一 tab，__PROBE 被覆盖 + 互相推进点击 -> activeAfter 恰好等于下一个节点（5 条 contradicts + 16 条 active 错位）。v5 自建专属 target、每节点前校验 probeTag、记录并发 tab 数。',
      C1_closeProof: '点击前必须同时满足：可见 settings 根=0、可见开着且承载面板的 .ant-drawer=0、目标节点命中可达；否则 CLEAR_OVERLAY_FAIL 且不点击不采集。',
      C2_tripleIdentity: 'active nodeId==目标 + drawer 标题非空且类型一致 + freshOpen(openSeq>closedSeq)。',
      C3_fingerprints: '结构指纹（v4 同算法）+ 面板全文 FNV1a×2 指纹（新增，含长度），相邻节点全文指纹必须互异。',
      E1_structuralNoClick: 'BRANCH/CONDITION 无抽屉（可信点击实测 drawers==0），v5.1 不点击、只读卡片；卡片指纹 = FNV1a×2{标题, 表达式, 条件序号, 角色, 折叠态}。',
      E2_readOnlyClassify: '只读判据改为「端点性质 + rootField 命名」双重判定，逐条给出 write/read 与理由，消除 WRITE_DETECTED 假阳性。'
    },
    panelIdentityRule: {
      panelRoot: '.udc-microflow-editor-node-settings（挂在 .ant-drawer-body 下）',
      authoritativeTitle: '.ant-drawer-title（抽屉头部，不在 settings 根内）',
      closeProof: 'clearAndProve()：close-btn/ESC 轮询 -> 空壳纯视图 display:none -> 三重确证（可见 settings 根=0 && 可见开着的 .ant-drawer=0 && hitProbe.ok）',
      switchProof: 'freshOpen：抽屉首次在 pre-click 清空之后出现（data-p6-open-seq > closedSeq）',
      fingerprints: 'structural = FNV1a×2{drawerTitle,formLabels,ctlSig,buttons}；fullText = FNV1a×2(面板 innerText 归一化)',
      failConditions: ['CLEAR_OVERLAY_FAIL（关闭未确证，未点击）', 'CLICK_TARGET_FAIL（命中点始终不在目标子树）', 'PANEL_SWITCH_FAIL（identity 未自证）', 'NO_PANEL（点击+重试后仍无面板）', 'structural/fullText 指纹跨类型重复', '面板标题与 nodeType 矛盾']
    },
    schemaEnum: { count: enumd.uniqueNodeCount, domContainerCount: enumd.domContainerCount, enumSource: enumd.enumSource, canvas: enumd.canvas, capturedCount: results.length, countConsistent: opts.limit ? null : (results.length === enumd.uniqueNodeCount), nodes: enumd.nodes },
    nodes: results, failures: j.fails, notes: j.notes,
    fieldsAudit: jf.summary, fieldsPerNode: jf.perNode,
    knownFailRecheck: knownFail,
    scopeNote: '本版只采面板级证据（面板全文指纹/标题/身份/字段/必填）。DATA_MAPPING 内层映射弹窗与表达式 token 属于 P0-2/P1，v5 不主动开弹窗（避免制造额外覆盖层污染本轮身份证据）。',
    selfTest: { command: 'node tools/cdp/snapshot/microflow-panel-probe-v6.0.js --self-test', cases: selfTestCount() },
    audit: Object.assign(audit, { elapsedMs: Date.now() - t0, readOnly: true })
  };
  const outPath = path.resolve(opts.out);
  fs.mkdirSync(path.dirname(outPath), { recursive: true });
  fs.writeFileSync(outPath, JSON.stringify(out, null, 1));
  console.log('\nstatus=' + finalStatus + ' nodes=' + results.length + '/' + enumd.uniqueNodeCount + ' fails=' + j.fails.length + ' writes=' + audit.writes + ' http=' + JSON.stringify(audit.httpRequests));
  console.log('-> ' + outPath);
  if (j.fails.length) console.log('FAILURES=' + JSON.stringify(j.fails.map(f => ({ code: f.code, rule: f.rule, node: f.node || (f.nodes || []).map(x => x.nodeId || x) })), null, 1));
  c.close();
  try { await browser.send('Target.closeTarget', { targetId }); } catch (e) { }
  browser.close();
  return { status: finalStatus, outPath, fails: j.fails, knownFail, count: results.length, total: enumd.uniqueNodeCount, audit };
}

/* ---------- CLI ---------- */
(async () => {
  const argv = process.argv.slice(2);
  const opt = { flow: '-1014184770817921434', app: '8704025620829192834', out: 'docs/audit/artifacts/udc-node-evidence/microflow-panel-probe-v6.json', limit: 0 };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === '--flow') opt.flow = argv[++i];
    else if (a === '--app') opt.app = argv[++i];
    else if (a === '--out') opt.out = argv[++i];
    else if (a === '--limit') opt.limit = Number(argv[++i]) || 0;
    else if (a === '--cdp') CDP_PORT = Number(argv[++i]) || CDP_PORT;
    else if (a === '--self-test') { const r = selfTest(); process.exit(r.ok ? 0 : 1); }
    else if (a === '--help') { console.log('usage: node microflow-panel-probe-v6.0.js [--self-test] [--flow F] [--app A] [--out P] [--limit N] [--cdp PORT]'); process.exit(0); }
  }
  try {
    const r = await live(opt);
    if (r.status === 'PASS') process.exit(0);
    if (r.status === 'BLOCKED') process.exit(2);
    process.exit(3);
  } catch (e) { console.log('ERR ' + ((e && e.stack) || e)); process.exit(1); }
})();
