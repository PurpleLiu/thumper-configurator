/* Thumper 選配器 — 規則引擎、清單產生、進度保存。資料在 data.js（tools/build.py 產生） */
(function () {
  'use strict';
  const D = window.THUMPER;
  const G = D.groups;
  const byId = Object.fromEntries(G.map(g => [g.id, g]));
  const SRC = { author: '作者', ours: '我們的經驗', guess: '推測' };
  const $ = s => document.querySelector(s);
  const esc = s => String(s == null ? '' : s).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
  const store = {
    get(k, d) { try { const v = localStorage.getItem('thumper:' + k); return v == null ? d : JSON.parse(v); } catch (e) { return d; } },
    set(k, v) { try { localStorage.setItem('thumper:' + k, JSON.stringify(v)); } catch (e) {} }
  };

  // ---------- 選擇狀態 ----------
  function defaults() {
    const s = {};
    G.forEach(g => { s[g.id] = g.type === 'many' ? [] : g.options[0].id; });
    return s;
  }
  let sel = Object.assign(defaults(), store.get('sel', {}));
  const fromHash = parseHash();
  if (fromHash) sel = Object.assign(defaults(), fromHash);

  const opt = (gid, oid) => byId[gid].options.find(o => o.id === oid);
  const selected = s => G.flatMap(g => (g.type === 'many' ? s[g.id] : [s[g.id]]).map(id => [g, opt(g.id, id)]).filter(x => x[1]));
  const matches = (when, s) => Object.entries(when || {}).every(([gid, ids]) => {
    const v = s[gid]; return Array.isArray(v) ? v.some(x => ids.includes(x)) : ids.includes(v);
  });
  const okFor = (o, s) => !o.onlyWith || matches(o.onlyWith, s);

  // 選了某個選項之後，讓其他群組跟著變成相容的；回傳改了哪些
  function apply(gid, oid) {
    const s = JSON.parse(JSON.stringify(sel));
    const g = byId[gid];
    if (g.type === 'many') {
      const i = s[gid].indexOf(oid);
      if (i >= 0) { s[gid].splice(i, 1); return finish(s, []); }
      s[gid].push(oid);
    } else s[gid] = oid;
    const changes = [];
    const me = opt(gid, oid);
    // 1) 自己的條件：把對應群組改成條件允許的第一個
    Object.entries(me.onlyWith || {}).forEach(([og, ids]) => {
      if (!matches({ [og]: ids }, s)) {
        const pick = ids.find(x => opt(og, x) && okFor(opt(og, x), Object.assign({}, s, { [og]: x }))) || ids[0];
        changes.push(`${byId[og].zh} → ${opt(og, pick).zh}`);
        s[og] = pick;
      }
    });
    // 2) 其他已選但變得不相容的，換成第一個相容的（單選）或取消（複選）
    for (let round = 0; round < 6; round++) {
      let moved = false;
      G.forEach(og => {
        if (og.id === gid) return;
        if (og.type === 'many') {
          const keep = s[og.id].filter(x => okFor(opt(og.id, x), s));
          s[og.id].filter(x => !keep.includes(x)).forEach(x => changes.push(`取消 ${opt(og.id, x).zh}`));
          if (keep.length !== s[og.id].length) { s[og.id] = keep; moved = true; }
        } else if (!okFor(opt(og.id, s[og.id]), s)) {
          const pick = og.options.find(o => okFor(o, s));
          if (pick) { changes.push(`${og.zh} → ${pick.zh}`); s[og.id] = pick.id; moved = true; }
        }
      });
      if (!moved) break;
    }
    return finish(s, changes);
  }
  function finish(s, changes) {
    sel = s; store.set('sel', sel); render();
    if (changes.length) toast('已自動調整：' + changes.join('；'));
  }

  // ---------- 清單計算 ----------
  function compute(s) {
    const sels = selected(s);
    const removes = new Set();
    const adds = [];           // [key, copies, 來源]
    sels.forEach(([g, o]) => {
      (o.remove || []).forEach(k => removes.add(k));
      (o.add || []).forEach(k => adds.push([k, (o.copies && o.copies[k]) || D.parts[k].n, o.zh]));
      (o.addIf || []).forEach(c => { if (matches(c.when, s)) c.add.forEach(k => adds.push([k, D.parts[k].n, o.zh])); });
      if (o.wheelset) {
        const w = o.ignoreWidth ? 'narrow' : s.width;
        const sets = w === 'both' ? ['narrow', 'wide'] : [w];
        sets.forEach(x => (o.wheelset[x] || []).forEach(k => adds.push([k, D.parts[k].n * 4, o.zh + '（' + (x === 'narrow' ? '窄胎' : '寬胎') + '）'])));
        (o.wheelset.shared || []).forEach(k => adds.push([k, D.parts[k].n * 4 * (w === 'both' && !o.ignoreWidth ? 2 : 1), o.zh]));
      }
    });
    const list = new Map();
    D.base.forEach(k => { if (!removes.has(k)) list.set(k, { n: D.parts[k].n, from: '主車' }); });
    adds.forEach(([k, n, from]) => {
      if (removes.has(k)) return;
      const cur = list.get(k);
      if (cur) { cur.n += (cur.from === from ? n : 0); if (cur.from !== from) cur.n = Math.max(cur.n, n); } else list.set(k, { n, from });
    });
    // 電變座
    const escSize = D.esc[s.motor];
    if (escSize && s.trans !== 'pr_g') list.set(D.escParts[escSize + (s.headlight === 'led' ? 'led' : '')], { n: 1, from: '電變座' });
    list.set(D.test, { n: 1, from: '先印：每種材料各 1 個' });
    // 採購
    const bom = new Map();
    const addB = (it, q, why) => { const c = bom.get(it) || { qty: 0, why: [] }; c.qty += q; if (why && !c.why.includes(why)) c.why.push(why); bom.set(it, c); };
    D.baseBom.forEach(b => addB(b.item, b.qty, '主車'));
    sels.forEach(([g, o]) => {
      const mult = (o.wheelset && !o.ignoreWidth && s.width === 'both') ? 2 : 1;  // 窄胎、寬胎兩組都印時，輪框螺絲加倍
      (o.bom || []).forEach(b => addB(b.item, b.qty * mult, o.zh));
      (o.bomIf || []).forEach(c => { if (matches(c.when, s)) c.bom.forEach(b => addB(b.item, b.qty, o.zh)); });
    });
    if (escSize) { addB('banana4', 1, '有電變'); }
    // 提醒
    const warns = [];
    sels.forEach(([g, o]) => (o.warn || []).forEach(w => { if (!w.when || matches(w.when, s)) warns.push({ text: w.text, src: w.src, from: o.zh, g: g.id }); }));
    if (s.trans === 'pr_g') warns.push({ text: '540 馬達佔掉電變座的位置：不印電變座，電變移到翼子板。', src: 'author', from: '列印齒輪 G', g: 'trans' });
    return { list, bom, warns };
  }

  // ---------- 畫面：選配 ----------
  function img(o) {
    const pics = [];
    if (o.photo) pics.push(`<img src="${o.photo}" alt="" loading="lazy">`);
    if (o.img) pics.push(`<img class="stl" src="${o.img}" alt="" loading="lazy">`);
    if (!pics.length) return '';
    return `<div class="pic ${pics.length > 1 ? 'two' : ''}">${pics.join('')}</div>`;
  }
  // 放大檢視用的照片：主照片＋參考照片；沒有照片時用 3D 預覽圖
  function shots(o) {
    const a = [];
    if (o.photo) a.push({ src: o.photo, cap: o.zh });
    (o.gallery || []).forEach(x => a.push(x));
    if (!a.length && o.img) a.push({ src: o.img, cap: o.zh + '（3D 預覽）' });
    return a;
  }
  let zoomList = [], zoomAt = 0;
  function zoomShow(i) {
    zoomAt = (i + zoomList.length) % zoomList.length;
    const z = zoomList[zoomAt];
    $('#zoom-img').src = z.src;
    $('#zoom-cap').textContent = (zoomList.length > 1 ? `${zoomAt + 1} / ${zoomList.length}　` : '') + z.cap;
    $('#zoom').classList.toggle('multi', zoomList.length > 1);
  }
  function renderGroups() {
    const res = compute(sel);
    $('#groups').innerHTML = G.map(g => {
      const cur = g.type === 'many' ? sel[g.id] : [sel[g.id]];
      const warns = res.warns.filter(w => w.g === g.id);
      return `<section class="group" id="g-${g.id}"><h2>${esc(g.zh)}<small>${g.type === 'many' ? '可複選' : '選一個'}</small></h2>
        <div class="opts">${g.options.map(o => {
          const on = cur.includes(o.id), ok = okFor(o, sel);
          const page = o.page && D.pages[o.page] ? `<a class="desc" href="${D.pages[o.page].url}" target="_blank" rel="noopener" onclick="event.stopPropagation()">Printables ${o.page} ↗</a><a class="desc" href="${D.pages[o.page].url}/makes" target="_blank" rel="noopener" onclick="event.stopPropagation()">網友作品照 ↗</a>` : '';
          return `<button type="button" class="opt ${ok ? '' : 'blocked'}" aria-pressed="${on}" data-g="${g.id}" data-o="${o.id}">
            ${img(o)}${shots(o).length ? `<span class="zoom" data-zoom="${g.id}|${o.id}">${shots(o).length > 1 ? '照片 ' + shots(o).length + ' 張' : '放大'}</span>` : ''}
            <span class="txt"><span class="name">${o.unofficial ? '<span class="tag unoff">非官方</span>' : ''}${esc(o.zh)}</span>
            ${o.desc ? `<span class="desc">${esc(o.desc)}</span>` : ''}
            ${ok ? '' : `<span class="why">${esc(o.why || '跟目前的選擇不相容')}，點了會自動調整其他選項</span>`}${page}</span></button>`;
        }).join('')}</div>
        ${warns.length ? `<ul class="warns">${warns.map(w => `<li><span class="tag ${w.src}">${SRC[w.src]}</span>${esc(w.text)}</li>`).join('')}</ul>` : ''}</section>`;
    }).join('');
  }
  function renderSummary() {
    const res = compute(sel);
    let pieces = 0; res.list.forEach(v => pieces += v.n);
    const printed = store.get('printed', {});
    let done = 0; res.list.forEach((v, k) => { if (printed[k]) done++; });
    const items = [...res.bom.entries()].filter(([, v]) => v.qty > 0);
    const bought = store.get('bought', {});
    $('#summary').innerHTML = `<h3>目前的配置</h3>
      <div class="stats"><div class="stat"><b>${res.list.size}</b><span>個 STL 檔（已印 ${done}）</span></div><div class="stat"><b>${pieces}</b><span>個零件要印</span></div>
      <div class="stat"><b>${items.length}</b><span>項要買（已買 ${items.filter(([k]) => bought[k]).length}）</span></div><div class="stat"><b>${res.warns.length}</b><span>則提醒</span></div></div>
      <ul class="chosen">${G.filter(g => g.type === 'one').map(g => `<li><span>${esc(g.zh)}</span>${esc(opt(g.id, sel[g.id]).zh)}</li>`).join('')}
      ${G.filter(g => g.type === 'many' && sel[g.id].length).map(g => `<li><span>${esc(g.zh)}</span>${sel[g.id].map(x => esc(opt(g.id, x).zh)).join('、')}</li>`).join('')}</ul>
      <div class="row"><button class="btn" data-go="print">看列印清單</button><button class="btn" data-go="bom">看採購清單</button></div>
      <div class="row"><button class="btn ghost" id="share">複製這個配置的網址</button><button class="btn ghost" id="reset">重設成預設</button></div>`;
    $('#mbar').innerHTML = `<span><b>${res.list.size}</b> 個檔・<b>${pieces}</b> 件・<b>${items.length}</b> 項要買</span><span><button class="btn" data-go="print">列印</button> <button class="btn" data-go="bom">採購</button></span>`;
    $('#badge-print').textContent = res.list.size;
    $('#badge-bom').textContent = items.length;
  }

  // ---------- 畫面：列印清單 ----------
  function renderPrint() {
    const res = compute(sel);
    const printed = store.get('printed', {});
    const onlyTodo = store.get('onlyTodo', false);
    const rows = [...res.list.entries()].map(([k, v]) => ({ k, v, p: D.parts[k] })).sort((a, b) => a.p.cat.localeCompare(b.p.cat) || a.p.file.localeCompare(b.p.file));
    let cat = '', html = '';
    rows.forEach(r => {
      if (onlyTodo && printed[r.k]) return;
      if (r.p.cat !== cat) { cat = r.p.cat; html += `<tr class="cat"><td colspan="7">${esc(cat.replace(/^\d /, ''))}</td></tr>`; }
      const pg = D.pages[r.p.page];
      html += `<tr class="${printed[r.k] ? 'done' : ''}"><td><input type="checkbox" aria-label="已印" data-pk="${esc(r.k)}" ${printed[r.k] ? 'checked' : ''}></td>
        <td>${esc(r.p.zh)}<div class="tip" style="color:var(--muted)">${esc(r.v.from)}</div></td><td class="file">${esc(r.p.file)}</td><td class="num">${r.v.n}</td>
        <td>${esc(r.p.ai)}<div class="tip"><span class="tag author">作者</span>強化 PLA</div></td>
        <td>${r.p.om ? `${esc(r.p.om)} ${esc(r.p.oi || '')}<div class="tip"><span class="tag ours">我們</span>${esc(r.p.ow || '')}</div>` : '<span style="color:var(--muted)">—</span>'}</td>
        <td><a href="${pg.url}" target="_blank" rel="noopener">${esc(pg.zh)} ↗</a>${pg.kind === 'third' ? '<div class="tip"><span class="tag unoff">非官方</span></div>' : ''}</td></tr>`;
    });
    let pieces = 0; res.list.forEach(v => pieces += v.n);
    $('#panel-print').innerHTML = `<h2 class="ph">列印清單</h2>
      <p class="pn">共 ${res.list.size} 個 STL 檔、${pieces} 個零件。請到每一列右邊連結的 Printables 頁面下載。「作者」欄是作者建議的填充（作者用強化 PLA 設計）；「我們」欄是社團分享者實際用的材質，只有做過的零件才有。檔名有 2X、4X 的檔案裡只有 1 個零件，要照份數印。</p>
      <div class="tools"><label><input type="checkbox" id="onlyTodo" ${onlyTodo ? 'checked' : ''}> 只看還沒印的</label>
      <button class="btn ghost" id="csv-print">下載 CSV</button><button class="btn ghost" id="clear-print">清除已印勾選</button></div>
      <div class="tblwrap"><table><thead><tr><th>已印</th><th>零件</th><th>檔名</th><th class="num">份數</th><th>作者建議填充</th><th>我們用的</th><th>下載頁</th></tr></thead><tbody>${html}</tbody></table></div>
      <h2 class="ph">列印設定</h2><div class="tips-grid"><div class="tipcard"><h3><span class="tag author">作者</span></h3>${esc(D.printSettings.author)}</div><div class="tipcard"><h3><span class="tag ours">我們的經驗</span></h3>${esc(D.printSettings.ours)}</div></div>`;
  }

  // ---------- 畫面：採購清單 ----------
  function buy(it, q) {
    if (/^m[2345]/.test(it) && q > 0) return Math.max(q + 5, Math.ceil(q * 1.2 / 10) * 10);
    return q;
  }
  function renderBom() {
    const res = compute(sel);
    const bought = store.get('bought', {});
    const rows = [...res.bom.entries()].filter(([, v]) => v.qty > 0).map(([k, v]) => ({ k, v, it: D.items[k] || { zh: k, cat: '其他', unit: '' } }))
      .sort((a, b) => a.it.cat.localeCompare(b.it.cat, 'zh-Hant') || a.it.zh.localeCompare(b.it.zh, 'zh-Hant'));
    let cat = '', html = '';
    rows.forEach(r => {
      if (r.it.cat !== cat) { cat = r.it.cat; html += `<tr class="cat"><td colspan="6">${esc(cat)}</td></tr>`; }
      const t = r.it.tip;
      html += `<tr class="${bought[r.k] ? 'done' : ''}"><td><input type="checkbox" aria-label="已買" data-bk="${esc(r.k)}" ${bought[r.k] ? 'checked' : ''}></td>
        <td>${esc(r.it.zh)}${t ? `<div class="tip"><span class="tag ${t[0]}">${SRC[t[0]]}</span>${esc(t[1])}</div>` : ''}</td>
        <td class="num">${r.v.qty}</td><td class="num">${buy(r.k, r.v.qty)} ${esc(r.it.unit || '')}</td>
        <td>${r.it.kw ? `<button class="kw" data-copy="${esc(r.it.kw)}" title="點一下複製">${esc(r.it.kw)}</button>` : ''}</td>
        <td style="font-size:12px;color:var(--muted)">${esc(r.v.why.join('、'))}</td></tr>`;
    });
    $('#panel-bom').innerHTML = `<h2 class="ph">採購清單</h2>
      <p class="pn">依作者各頁的零件表加總；Full Top 和車門作者沒列螺絲，是社團分享者從零件孔位估的。螺絲「建議購買」已多加約 20% 備品。遙控器、接收器、充電器、工具沒有列在這裡。搜尋關鍵字是淘寶用的簡體，點一下就能複製。</p>
      <div class="tools"><button class="btn ghost" id="csv-bom">下載 CSV</button><button class="btn ghost" id="copy-bom">複製還沒買的</button><button class="btn ghost" id="clear-bom">清除已買勾選</button></div>
      <div class="tblwrap"><table><thead><tr><th>已買</th><th>品項</th><th class="num">需求</th><th class="num">建議購買</th><th>淘寶關鍵字</th><th>哪個選項需要</th></tr></thead><tbody>${html}</tbody></table></div>
      <p class="pn">工具：手鑽和 2.5mm 鑽頭、銼刀、虎鉗或夾具、尖嘴鉗、美工刀、內六角起子（1.5／2／2.5mm）、烙鐵、剝線鉗、鋼鋸或電磨（切 5mm 棒）、100 號砂紙。</p>`;
  }

  // ---------- 畫面：避坑指南與來源 ----------
  function renderTips() {
    const by = {};
    D.pitfalls.forEach(([c, t, s]) => (by[c] = by[c] || []).push([t, s]));
    const pages = Object.entries(D.pages);
    const pg = kind => pages.filter(([, p]) => p.kind === kind).map(([id, p]) => `<a href="${p.url}" target="_blank" rel="noopener"><b>${esc(p.zh)} ↗</b>${esc(p.name)}<br><span style="color:var(--muted)">${esc(p.author)}・${p.count} 個檔・最新檔案 ${p.updated}</span></a>`).join('');
    $('#panel-tips').innerHTML = `<h2 class="ph">避坑指南</h2><p class="pn">社團分享者實際做完一台的經驗，加上作者頁面和留言裡的重點。</p>
      <div class="tips-grid">${Object.entries(by).map(([c, l]) => `<div class="tipcard"><h3>${esc(c)}</h3><ul style="margin:0;padding-left:1.1em;display:grid;gap:6px">${l.map(([t, s]) => `<li><span class="tag ${s}">${SRC[s]}</span>${esc(t)}</li>`).join('')}</ul></div>`).join('')}</div>
      <h2 class="ph">組裝遇到問題時</h2><p class="pn">作者的 <a href="https://www.printables.com/model/396992" target="_blank" rel="noopener">Requested and Retired parts（396992）↗</a> 放了修正件：球頭太緊卡死的縮小版連桿（0.1／0.2mm）、螺帽槽加大的橋殼、用 7×14×5 軸承的橋殼、軸承孔放鬆的差速殼、反向輪轂、半頂後車斗無支撐版。不是選配，遇到問題再去找。</p>
      <h2 class="ph">官方頁面（BlackCrow）</h2><div class="pages">${pg('official')}</div>
      <h2 class="ph">非官方頁面</h2><div class="pages">${pg('third')}</div>`;
  }

  // ---------- 畫面：組裝步驟 ----------
  const A = D.assembly;
  // when／unless：{群組: [選項]}；any 為 true 時任一群組符合就算
  const part1 = (w, s, any) => any ? Object.entries(w).some(([g, ids]) => matches({ [g]: ids }, s)) : matches(w, s);
  const cond = (x, s) => (!x.when || part1(x.when, s, x.any)) && (!x.unless || !part1(x.unless, s, x.any));
  const ytUrl = id => 'https://www.youtube.com/watch?v=' + id;
  const srcTag = s => s ? `<span class="tag ${s}">${SRC[s]}</span>` : '';
  function vcard(v) {
    return `<a class="vcard ${v.old ? 'old' : ''}" href="${ytUrl(v.id)}" target="_blank" rel="noopener"><img src="https://i.ytimg.com/vi/${v.id}/mqdefault.jpg" alt="" loading="lazy"><span>${v.old ? '<span class="tag guess">舊版</span>' : ''}${esc(v.zh)} ↗</span></a>`;
  }
  function renderAssembly() {
    const res = compute(sel), done = store.get('steps', {}), printed = store.get('printed', {}), open = store.get('openStages', {});
    const stages = A.stages.filter(st => cond(st, sel));
    let all = 0, ok = 0;
    const cards = stages.map((st, i) => {
      const steps = st.steps.filter(x => cond(x, sel)), warns = st.warns.filter(x => cond(x, sel)), vids = st.videos.filter(x => cond(x, sel));
      const ps = [...res.list.entries()].filter(([k]) => D.parts[k].stage === st.id);
      const n = steps.filter(x => done[st.id + ':' + x.id]).length; all += steps.length; ok += n;
      const isOpen = open[st.id] !== undefined ? open[st.id] : n < steps.length;
      return `<details class="stage ${n === steps.length && steps.length ? 'done' : ''}" data-stage="${st.id}" ${isOpen ? 'open' : ''}>
        <summary><span class="sn">${i + 1}</span><span class="st">${esc(st.zh)}</span><span class="sc">${n} / ${steps.length}</span></summary>
        ${vids.length ? `<div class="vids">${vids.map(vcard).join('')}</div>` : ''}
        <ol class="steps">${steps.map(x => { const k = st.id + ':' + x.id; return `<li><label><input type="checkbox" data-step="${esc(k)}" ${done[k] ? 'checked' : ''}><span>${srcTag(x.src)}${esc(x.text)}</span></label></li>`; }).join('')}</ol>
        ${warns.length ? `<ul class="warns">${warns.map(w => `<li>${srcTag(w.src)}${esc(w.text)}</li>`).join('')}</ul>` : ''}
        ${ps.length ? `<div class="sparts"><b>這一段用到的列印件（${ps.filter(([k]) => printed[k]).length} / ${ps.length} 已印）</b>${ps.map(([k, v]) => `<span class="chip ${printed[k] ? 'ok' : ''}" title="${esc(D.parts[k].file)}">${esc(D.parts[k].zh)}${v.n > 1 ? ' ×' + v.n : ''}</span>`).join('')}</div>` : ''}
      </details>`;
    }).join('');
    const extra = [...res.list.keys()].filter(k => D.parts[k].stage === 'extra');
    $('#panel-steps').innerHTML = `<h2 class="ph">組裝步驟</h2>
      <p class="pn">照作者影片的順序：先車身、再底盤。步驟、影片和注意事項會跟著你的選配變。作者的主車影片 1–8 是用原版零件拍的，換了選配的地方看該階段列的配件影片。完成的步驟打勾會存在這台裝置的瀏覽器裡。</p>
      <div class="tools"><span class="prog"><b>${ok}</b> / ${all} 步完成</span><button class="btn ghost" id="steps-open">全部展開</button><button class="btn ghost" id="steps-close">全部收合</button><button class="btn ghost" id="clear-steps">清除打勾</button></div>
      ${cards}
      ${extra.length ? `<div class="sparts"><b>其他配件（照各自頁面說明安裝）</b>${extra.map(k => `<span class="chip">${esc(D.parts[k].zh)}</span>`).join('')}</div>` : ''}`;
  }

  // ---------- 畫面：影片 ----------
  function renderVideos() {
    const showAll = store.get('allVideos', false), seen = new Set();
    const sec = (title, vids) => vids.length ? `<h3 class="vh">${esc(title)}</h3><div class="vids">${vids.map(vcard).join('')}</div>` : '';
    let html = '';
    A.stages.forEach(st => {
      const vids = st.videos.filter(v => !seen.has(v.id) && (showAll || (cond(st, sel) && cond(v, sel))));
      vids.forEach(v => seen.add(v.id));
      html += sec(st.zh, vids);
    });
    const cats = {};
    A.extraVideos.filter(v => showAll || cond(v, sel)).forEach(v => (cats[v.cat] = cats[v.cat] || []).push(v));
    Object.entries(cats).forEach(([c, v]) => html += sec(c, v));
    $('#panel-videos').innerHTML = `<h2 class="ph">官方影片</h2>
      <p class="pn">全部是作者 BlackCrow 的 YouTube 頻道（<a href="https://www.youtube.com/@RockyTop_BC" target="_blank" rel="noopener">@RockyTop_BC ↗</a>）。預設只列你目前配置用得到的；標「舊版」的是作者重拍前的版本，零件可能跟現在的檔案不同。作者的播放清單：<a href="https://www.youtube.com/playlist?list=PL0AxX5F7uSsIER_8jmnkl3Xip5-CC_HGB" target="_blank" rel="noopener">主車組裝 ↗</a>、<a href="https://www.youtube.com/playlist?list=PL0AxX5F7uSsIGvmditFgBaNI6SvXfX3Xt" target="_blank" rel="noopener">4WS ↗</a>、<a href="https://www.youtube.com/playlist?list=PL0AxX5F7uSsL8j9zIhX_MDsKrEGC6mMlS" target="_blank" rel="noopener">車門與車頂 ↗</a>。</p>
      <div class="tools"><label><input type="checkbox" id="allVideos" ${showAll ? 'checked' : ''}> 顯示全部影片（含跟你配置無關的）</label></div>${html}`;
  }

  // ---------- 畫面：齒比計算 ----------
  function renderCalc() {
    const c = Object.assign({ axle: 33, tire: 120, cells: 2 }, store.get('calc', {}));
    const tr = A.ratio[sel.trans], kvDef = A.kv[sel.motor];
    const ratio = c.ratioOverride || tr || 4, kv = c.kvOverride || kvDef || 1200;
    const fin = ratio * (c.axle / 8), circ = Math.PI * c.tire, mm = circ / fin;
    const kmh = kv * c.cells * 3.7 / fin * circ * 60 / 1e6;
    const trans = opt('trans', sel.trans), motor = opt('motor', sel.motor);
    const band = mm < 17 ? '純攀爬（作者 A 變速箱的範圍）' : mm <= 26 ? '攀爬兼跑（作者 B 變速箱的範圍）' : '高速跑（作者 C 變速箱的範圍，不適合攀爬）';
    $('#panel-calc').innerHTML = `<h2 class="ph">齒比與推進距離</h2>
      <p class="pn">作者用「馬達轉一圈，車子前進幾 mm」比較各種配置：數字越小越慢、越好控制。總減速比 = 變速箱 × 車橋（大齒輪 ÷ 8T）；推進距離 = 輪胎周長 ÷ 總減速比。變速箱和馬達 KV 先照你的選配帶入，也可以自己改。</p>
      <div class="calc">
        <div class="cin">
          <label>變速箱減速比<input type="number" step="0.01" min="1" id="c-ratio" value="${ratio}"><small>${esc(trans.zh)}${tr ? `（作者：${tr}:1）` : ''}</small></label>
          <label>車橋傘齒<select id="c-axle">${A.axle.map(([t, zh]) => `<option value="${t}" ${t === c.axle ? 'selected' : ''}>${esc(zh)}</option>`).join('')}</select></label>
          <label>輪胎外徑（mm）<input type="number" step="1" min="80" max="200" id="c-tire" value="${c.tire}"><small>作者的 1.9 吋胎是 120mm</small></label>
          <label>馬達 KV<input type="number" step="10" min="100" id="c-kv" value="${kv}"><small>${esc(motor.zh)}${kvDef ? '' : '（這顆馬達沒有固定 KV，請自己填）'}</small></label>
          <label>電池<select id="c-cells"><option value="2" ${c.cells === 2 ? 'selected' : ''}>2S（7.4V）</option><option value="3" ${c.cells === 3 ? 'selected' : ''}>3S（11.1V）</option></select></label>
          <button class="btn ghost" id="c-reset">照選配重新帶入</button>
        </div>
        <div class="cout">
          <div class="stat"><span>總減速比</span><b>${fin.toFixed(1)} : 1</b><small>${ratio} × ${(c.axle / 8).toFixed(3)}</small></div>
          <div class="stat"><span>馬達每轉前進</span><b>${mm.toFixed(1)} mm</b><small>${band}</small></div>
          <div class="stat"><span>理論極速（無負載）</span><b>${kmh.toFixed(1)} km/h</b><small>KV × 電壓換算；實際跑起來會再慢一些</small></div>
        </div>
      </div>
      <h3 class="vh">作者的對照表（120mm 輪胎）<span class="tag author">作者</span></h3>
      <div class="tblwrap"><table><thead><tr><th>變速箱</th><th>車橋</th><th class="num">總減速比</th><th class="num">每轉前進</th></tr></thead><tbody>
      ${[['列印 A（7.5:1）', 7.5], ['列印 B（5:1）', 5], ['列印 C（1.86:1）', 1.86]].flatMap(([n, r]) => [33, 30, 27, 24].map(t => `<tr><td>${n}</td><td>8T-${t}T</td><td class="num">${(r * t / 8).toFixed(1)}</td><td class="num">${(120 * Math.PI / (r * t / 8)).toFixed(0)} mm</td></tr>`)).join('')}
      </tbody></table></div>
      <p class="pn">金屬齒輪 A2／A540 是 6.25:1、B2／B540／B540C 是 4:1、C2 是 2:1（作者 769045 頁面）。</p>`;
  }

  // ---------- 匯出、分享 ----------
  function csv(name, head, rows) {
    const s = '﻿' + [head, ...rows].map(r => r.map(x => '"' + String(x == null ? '' : x).replace(/"/g, '""') + '"').join(',')).join('\r\n');
    const a = document.createElement('a');
    a.href = URL.createObjectURL(new Blob([s], { type: 'text/csv;charset=utf-8' })); a.download = name; a.click();
    setTimeout(() => URL.revokeObjectURL(a.href), 1000);
  }
  function hashOf(s) {
    return 'c=' + G.map(g => g.id + '.' + (g.type === 'many' ? s[g.id].join('~') : s[g.id])).join('_');
  }
  function parseHash() {
    const m = location.hash.match(/c=([A-Za-z0-9_.~-]+)/);
    if (!m) return null;
    const s = {};
    m[1].split('_').forEach(p => { const [gid, v] = p.split('.'); if (byId[gid]) s[gid] = byId[gid].type === 'many' ? (v ? v.split('~').filter(x => opt(gid, x)) : []) : (opt(gid, v) ? v : undefined); });
    Object.keys(s).forEach(k => s[k] === undefined && delete s[k]);
    return s;
  }
  function copy(text, ok) {
    const done = () => toast(ok || '已複製');
    if (navigator.clipboard && navigator.clipboard.writeText) navigator.clipboard.writeText(text).then(done, () => prompt('請手動複製', text));
    else prompt('請手動複製', text);
  }
  let tt;
  function toast(t) { const el = $('#toast'); el.textContent = t; el.hidden = false; clearTimeout(tt); tt = setTimeout(() => el.hidden = true, 4500); }

  // ---------- 分頁、事件 ----------
  let tab = store.get('tab', 'config');
  function show(t) {
    tab = t; store.set('tab', t);
    document.querySelectorAll('.tabs button').forEach(b => b.setAttribute('aria-selected', String(b.dataset.tab === t)));
    document.querySelectorAll('.panel').forEach(p => p.hidden = p.id !== 'panel-' + t);
    render(); window.scrollTo({ top: document.querySelector('.tabs').offsetTop - 4 });
  }
  function render() {
    renderSummary();
    if (tab === 'config') renderGroups();
    if (tab === 'print') renderPrint();
    if (tab === 'bom') renderBom();
    if (tab === 'tips') renderTips();
    if (tab === 'steps') renderAssembly();
    if (tab === 'videos') renderVideos();
    if (tab === 'calc') renderCalc();
  }
  $('#presets').innerHTML = '<span class="lbl">一鍵套用：</span>' + D.presets.map(p => `<button class="btn" data-preset="${p.id}" title="${esc(p.desc)}">${esc(p.zh)}</button>`).join('');
  document.addEventListener('click', e => {
    const t = e.target;
    const z = t.closest('[data-zoom]');
    if (z) {
      e.stopPropagation();
      const [gid, oid] = z.dataset.zoom.split('|');
      zoomList = shots(G.find(x => x.id === gid).options.find(x => x.id === oid));
      zoomShow(0); $('#zoom').showModal(); return;
    }
    if (t.id === 'zoom-prev') return zoomShow(zoomAt - 1);
    if (t.id === 'zoom-next') return zoomShow(zoomAt + 1);
    const o = t.closest('.opt');
    if (o) return apply(o.dataset.g, o.dataset.o);
    const tb = t.closest('.tabs button'); if (tb) return show(tb.dataset.tab);
    const go = t.closest('[data-go]'); if (go) return show(go.dataset.go);
    const pr = t.closest('[data-preset]');
    if (pr) { const p = D.presets.find(x => x.id === pr.dataset.preset); sel = Object.assign(defaults(), JSON.parse(JSON.stringify(p.sel))); store.set('sel', sel); render(); toast('已套用：' + p.zh + (p.notes ? '。' + p.notes.join(' ') : '')); return; }
    if (t.id === 'share') { const u = location.href.split('#')[0] + '#' + hashOf(sel); history.replaceState(null, '', u); return copy(u, '已複製配置網址，貼給別人就能看到同一個配置'); }
    if (t.id === 'reset') { sel = defaults(); store.set('sel', sel); render(); return; }
    if (t.dataset.copy) return copy(t.dataset.copy, '已複製：' + t.dataset.copy);
    if (t.id === 'clear-print') { store.set('printed', {}); return render(); }
    if (t.id === 'clear-steps') { store.set('steps', {}); return render(); }
    if (t.id === 'steps-open' || t.id === 'steps-close') { const o = {}; A.stages.forEach(st => o[st.id] = t.id === 'steps-open'); store.set('openStages', o); return render(); }
    if (t.id === 'c-reset') { store.set('calc', {}); return render(); }
    if (t.id === 'clear-bom') { store.set('bought', {}); return render(); }
    if (t.id === 'csv-print') {
      const r = compute(sel), pr2 = store.get('printed', {});
      return csv('Thumper列印清單.csv', ['分類', '零件', '檔名', '份數', '作者建議填充', '我們用的材質', '我們的填充', '下載頁', '已印'],
        [...r.list.entries()].map(([k, v]) => { const p = D.parts[k]; return [p.cat.replace(/^\d /, ''), p.zh, p.file, v.n, p.ai, p.om || '', p.oi || '', D.pages[p.page].url, pr2[k] ? '是' : '']; }));
    }
    if (t.id === 'csv-bom' || t.id === 'copy-bom') {
      const r = compute(sel), b2 = store.get('bought', {});
      const rows = [...r.bom.entries()].filter(([, v]) => v.qty > 0).map(([k, v]) => { const it = D.items[k] || { zh: k, cat: '' }; return [it.cat, it.zh, v.qty, buy(k, v.qty), it.unit || '', it.kw || '', b2[k] ? '是' : '']; });
      if (t.id === 'csv-bom') return csv('Thumper採購清單.csv', ['分類', '品項', '需求', '建議購買', '單位', '淘寶關鍵字', '已買'], rows);
      return copy(rows.filter(x => !x[6]).map(x => `${x[1]} ×${x[3]}${x[4]}${x[5] ? '（' + x[5] + '）' : ''}`).join('\n'), '已複製還沒買的品項');
    }
  });
  document.addEventListener('change', e => {
    const t = e.target;
    if (t.dataset.pk) { const p = store.get('printed', {}); p[t.dataset.pk] = t.checked; store.set('printed', p); return render(); }
    if (t.dataset.bk) { const b = store.get('bought', {}); b[t.dataset.bk] = t.checked; store.set('bought', b); return render(); }
    if (t.id === 'onlyTodo') { store.set('onlyTodo', t.checked); return render(); }
    if (t.dataset.step) { const d = store.get('steps', {}); d[t.dataset.step] = t.checked; store.set('steps', d); return render(); }
    if (t.id === 'allVideos') { store.set('allVideos', t.checked); return render(); }
    if (t.id && t.id.startsWith('c-')) {
      const c = store.get('calc', {}), v = parseFloat(t.value);
      ({ 'c-ratio': 'ratioOverride', 'c-kv': 'kvOverride', 'c-axle': 'axle', 'c-tire': 'tire', 'c-cells': 'cells' })[t.id] && (c[{ 'c-ratio': 'ratioOverride', 'c-kv': 'kvOverride', 'c-axle': 'axle', 'c-tire': 'tire', 'c-cells': 'cells' }[t.id]] = v);
      store.set('calc', c); return render();
    }
  });
  document.addEventListener('toggle', e => {
    const d = e.target; if (!d.dataset || !d.dataset.stage) return;
    const o = store.get('openStages', {}); o[d.dataset.stage] = d.open; store.set('openStages', o);
  }, true);
  $('#zoom-close').addEventListener('click', () => $('#zoom').close());
  $('#zoom').addEventListener('click', e => { if (e.target.id === 'zoom') $('#zoom').close(); });
  $('#zoom').addEventListener('keydown', e => {
    if (e.key === 'ArrowLeft') zoomShow(zoomAt - 1);
    if (e.key === 'ArrowRight') zoomShow(zoomAt + 1);
  });
  $('#foot').innerHTML = `資料來源：BlackCrow（BlackCrowRockyTop）在 Printables 的官方頁面和其他作者的非官方頁面，${esc(D.fetched)} 整理。STL 檔案請到原頁面下載；作者不同意檔案被搬到其他網站，這裡只放清單和連結。照片和 3D 預覽圖版權屬於原作者。`;
  if (fromHash) toast('已載入分享的配置');
  show(tab);
})();
