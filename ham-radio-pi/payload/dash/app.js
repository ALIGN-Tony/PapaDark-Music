/* HamPi dashboard frontend.
   - Widget windows: drag by title bar, resize by corner, z-order on tap.
     Layout persists per device in localStorage.
   - Phone (<720px): widgets stack full-width, drag/resize off.
   - On-screen keyboard: appears for text fields on touch; the moment a USB or
     Bluetooth keyboard is present (server-detected or a real keypress is seen)
     the physical keyboard wins and the OSK stays hidden. ⌨ button overrides. */

"use strict";

const $ = (s, r = document) => r.querySelector(s);

function h(tag, attrs = {}, ...kids) {
  const el = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (k === "class") el.className = v;
    else if (k.startsWith("on")) el.addEventListener(k.slice(2), v);
    else if (v !== null && v !== undefined) el.setAttribute(k, v);
  }
  for (const kid of kids) {
    if (kid === null || kid === undefined) continue;
    el.append(kid.nodeType ? kid : document.createTextNode(kid));
  }
  return el;
}

async function api(path, opts) {
  const r = await fetch(path, opts);
  let body = null;
  try { body = await r.json(); } catch (e) { /* non-JSON error page */ }
  if (!r.ok) throw new Error((body && body.error) || `${r.status} ${r.statusText}`);
  return body;
}

const cssVar = name => getComputedStyle(document.body).getPropertyValue(name).trim();

/* ---------------- Layout persistence ---------------- */

const LS_KEY = "hampi-dash-v1";
let layout = { open: ["prop", "power", "rig", "log"], geo: {}, night: false, kbMode: "auto" };
try {
  const saved = JSON.parse(localStorage.getItem(LS_KEY));
  if (saved && Array.isArray(saved.open)) layout = Object.assign(layout, saved);
} catch (e) { /* fresh start */ }
const soloMode = new URLSearchParams(location.search).has("solo");
function saveLayout() {
  if (soloMode) return;   // a ?solo kiosk view never rewrites the saved layout
  try { localStorage.setItem(LS_KEY, JSON.stringify(layout)); } catch (e) { /* private mode */ }
}

const stackedQuery = matchMedia("(max-width: 719px)");
const isStacked = () => stackedQuery.matches;

/* ---------------- Window manager ---------------- */

const desk = $("#desk");
const openWins = new Map();   // id -> {el, timer, widget}
let zTop = 10;

function clampGeo(g) {
  const W = desk.clientWidth || innerWidth, H = desk.clientHeight || (innerHeight - 58);
  g.w = Math.min(Math.max(g.w, 260), W);
  g.h = Math.min(Math.max(g.h, 140), H);
  g.x = Math.min(Math.max(g.x, 0), Math.max(0, W - 120));
  g.y = Math.min(Math.max(g.y, 0), Math.max(0, H - 48));
  return g;
}

const placeCursor = { x: 16, y: 16, rowH: 0 };
function defaultGeo(widget) {
  const W = desk.clientWidth || innerWidth;
  const w = widget.w || 400, ht = widget.h || 320;
  if (placeCursor.x > 16 && placeCursor.x + w > W - 8) {
    placeCursor.x = 16;
    placeCursor.y += placeCursor.rowH + 12;
    placeCursor.rowH = 0;
  }
  const H = desk.clientHeight || (innerHeight - 58);
  const g = clampGeo({ x: placeCursor.x,
                       y: Math.max(8, Math.min(placeCursor.y, H - ht - 8)),
                       w, h: ht });
  placeCursor.x += g.w + 12;
  placeCursor.rowH = Math.max(placeCursor.rowH, g.h);
  return g;
}

function openWidget(id) {
  if (openWins.has(id)) { raise(openWins.get(id).el); return; }
  const widget = WIDGETS[id];
  if (!widget) return;

  const body = h("div", { class: "win-body" });
  const win = h("div", { class: "win", "data-id": id },
    h("div", { class: "win-head" },
      h("span", { class: "win-title" }, `${widget.icon} ${widget.title}`),
      h("button", { class: "win-btn", title: "Refresh", onclick: () => entry.refresh() }, "⟳"),
      h("button", { class: "win-btn", title: "Close", onclick: () => closeWidget(id) }, "✕")),
    body,
    h("div", { class: "win-resize" }, "◢"));

  const g = clampGeo(layout.geo[id] || defaultGeo(widget));
  layout.geo[id] = g;
  Object.assign(win.style, { left: g.x + "px", top: g.y + "px", width: g.w + "px", height: g.h + "px" });
  win.addEventListener("pointerdown", () => raise(win));
  makeDraggable(win, g);
  desk.append(win);

  const entry = { el: win, widget, refresh: () => {}, timer: null };
  openWins.set(id, entry);
  const ctl = widget.build(body, entry) || {};
  entry.refresh = ctl.refresh || (() => {});
  entry.refresh();
  if (ctl.every) entry.timer = setInterval(() => entry.refresh(), ctl.every * 1000);

  if (!layout.open.includes(id)) layout.open.push(id);
  saveLayout();
  raise(win);
}

function closeWidget(id) {
  const entry = openWins.get(id);
  if (!entry) return;
  if (entry.timer) clearInterval(entry.timer);
  entry.el.remove();
  openWins.delete(id);
  layout.open = layout.open.filter(x => x !== id);
  saveLayout();
  renderLauncherGrid();
}

function raise(win) { win.style.zIndex = ++zTop; }

function makeDraggable(win, g) {
  const head = $(".win-head", win);
  const grip = $(".win-resize", win);
  const track = (el, onMove) => {
    el.addEventListener("pointerdown", e => {
      if (isStacked() || e.target.closest(".win-btn")) return;
      e.preventDefault();
      el.setPointerCapture(e.pointerId);
      const sx = e.clientX, sy = e.clientY, og = { ...g };
      const move = ev => { onMove(og, ev.clientX - sx, ev.clientY - sy); applyGeo(); };
      const up = () => {
        el.removeEventListener("pointermove", move);
        el.removeEventListener("pointerup", up);
        saveLayout();
      };
      el.addEventListener("pointermove", move);
      el.addEventListener("pointerup", up);
    });
  };
  const applyGeo = () => {
    clampGeo(g);
    Object.assign(win.style, { left: g.x + "px", top: g.y + "px", width: g.w + "px", height: g.h + "px" });
  };
  track(head, (og, dx, dy) => { g.x = og.x + dx; g.y = og.y + dy; });
  track(grip, (og, dx, dy) => { g.w = og.w + dx; g.h = og.h + dy; });
}

function applyStackMode() {
  document.body.classList.toggle("stack", isStacked());
}
stackedQuery.addEventListener("change", applyStackMode);
addEventListener("resize", () => {
  for (const [id, entry] of openWins) {
    const g = layout.geo[id];
    if (!g || isStacked()) continue;
    clampGeo(g);
    Object.assign(entry.el.style, { left: g.x + "px", top: g.y + "px" });
  }
});

/* ---------------- Charts (single series, hover/touch tooltip) ---------------- */

function lineChart(wrap, canvas, data, opts) {
  // data: {xs:[], ys:[]}; opts: {yUnit, xLabel(x), yFmt(y)}
  const ctx = canvas.getContext("2d");
  let tip = $(".tooltip", wrap);
  if (!tip) { tip = h("div", { class: "tooltip", hidden: "" }); wrap.append(tip); }

  function draw(markIdx = -1) {
    const dpr = devicePixelRatio || 1;
    const W = canvas.clientWidth, H = canvas.clientHeight;
    if (!W) return;
    canvas.width = W * dpr; canvas.height = H * dpr;
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.clearRect(0, 0, W, H);
    const { xs, ys } = data;
    if (xs.length < 2) {
      ctx.fillStyle = cssVar("--text-2"); ctx.font = "13px system-ui";
      ctx.fillText("collecting data…", 10, H / 2);
      return;
    }
    const pad = { l: 44, r: 8, t: 8, b: 18 };
    const ymin = Math.min(...ys), ymax = Math.max(...ys);
    const yr = (ymax - ymin) || 1;
    const X = i => pad.l + (W - pad.l - pad.r) * (i / (xs.length - 1));
    const Y = v => pad.t + (H - pad.t - pad.b) * (1 - (v - ymin) / yr);

    ctx.strokeStyle = cssVar("--border"); ctx.lineWidth = 1;
    ctx.beginPath();
    for (const v of [ymin, ymax]) { ctx.moveTo(pad.l, Y(v)); ctx.lineTo(W - pad.r, Y(v)); }
    ctx.stroke();
    ctx.fillStyle = cssVar("--text-2"); ctx.font = "11px system-ui";
    ctx.fillText(opts.yFmt(ymax), 4, Y(ymax) + 4);
    ctx.fillText(opts.yFmt(ymin), 4, Y(ymin) + 4);
    ctx.fillText(opts.xLabel(xs[0]), pad.l, H - 5);
    const endLabel = opts.xLabel(xs[xs.length - 1]);
    ctx.fillText(endLabel, W - pad.r - ctx.measureText(endLabel).width, H - 5);

    ctx.strokeStyle = cssVar("--chart"); ctx.lineWidth = 2;
    ctx.lineJoin = "round";
    ctx.beginPath();
    ys.forEach((v, i) => i ? ctx.lineTo(X(i), Y(v)) : ctx.moveTo(X(i), Y(v)));
    ctx.stroke();

    if (markIdx >= 0) {
      ctx.strokeStyle = cssVar("--text-2");
      ctx.setLineDash([3, 3]);
      ctx.beginPath(); ctx.moveTo(X(markIdx), pad.t); ctx.lineTo(X(markIdx), H - pad.b); ctx.stroke();
      ctx.setLineDash([]);
      ctx.fillStyle = cssVar("--chart");
      ctx.beginPath(); ctx.arc(X(markIdx), Y(ys[markIdx]), 4.5, 0, 7); ctx.fill();
      ctx.strokeStyle = cssVar("--card"); ctx.lineWidth = 2; ctx.stroke();
      tip.hidden = false;
      tip.textContent = `${opts.xLabel(xs[markIdx])} · ${opts.yFmt(ys[markIdx])}${opts.yUnit || ""}`;
      tip.style.left = X(markIdx) + "px";
      tip.style.top = Y(ys[markIdx]) + "px";
    } else {
      tip.hidden = true;
    }
  }

  canvas.addEventListener("pointermove", e => {
    if (data.xs.length < 2) return;
    const r = canvas.getBoundingClientRect();
    const frac = (e.clientX - r.left - 44) / (r.width - 52);
    draw(Math.round(Math.min(1, Math.max(0, frac)) * (data.xs.length - 1)));
  });
  canvas.addEventListener("pointerleave", () => draw(-1));
  new ResizeObserver(() => draw(-1)).observe(canvas);
  return { draw, data };
}

/* ---------------- Widgets ---------------- */

function preBox() { return h("pre", { class: "mono" }, " "); }
function kv(label, value, id) {
  return h("div", { class: "kv" }, h("b", id ? { id } : {}, value), h("span", {}, label));
}
const badge = level => h("span",
  { class: "badge " + (level === "OK" ? "ok" : level === "WARN" ? "warn" : "bad") },
  level === "OK" ? "✓ OK" : level === "WARN" ? "⚠ LOW" : "✖ CRITICAL");

const DEG = Math.PI / 180;

function gridToLatlon(grid) {
  const g = grid.trim().toUpperCase();
  if (g.length < 4) return null;
  let lon = (g.charCodeAt(0) - 65) * 20 - 180 + Number(g[2]) * 2;
  let lat = (g.charCodeAt(1) - 65) * 10 - 90 + Number(g[3]);
  if (g.length >= 6) {
    lon += (g.charCodeAt(4) - 65) * 5 / 60 + 2.5 / 60;
    lat += (g.charCodeAt(5) - 65) * 2.5 / 60 + 1.25 / 60;
  } else { lon += 1; lat += 0.5; }
  return Number.isFinite(lat + lon) ? [lat, lon] : null;
}

function greatCircle(lat1, lon1, lat2, lon2) {
  const p1 = lat1 * DEG, p2 = lat2 * DEG, dl = (lon2 - lon1) * DEG;
  const y = Math.sin(dl) * Math.cos(p2);
  const x = Math.cos(p1) * Math.sin(p2) - Math.sin(p1) * Math.cos(p2) * Math.cos(dl);
  const az = (Math.atan2(y, x) / DEG + 360) % 360;
  const km = 6371 * Math.acos(Math.max(-1, Math.min(1,
    Math.sin(p1) * Math.sin(p2) + Math.cos(p1) * Math.cos(p2) * Math.cos(dl))));
  return [Math.round(az), Math.round(km)];
}

function subsolarPoint(date) {
  // NOAA low-precision solar position; ~0.1-0.3 deg - plenty for a grayline.
  const d = (date.getTime() - Date.UTC(2000, 0, 1, 12)) / 86400000;
  const g = ((357.528 + 0.9856003 * d) % 360) * DEG;
  const L = (280.460 + 0.9856474 * d) % 360;
  const lambda = (L + 1.915 * Math.sin(g) + 0.020 * Math.sin(2 * g)) * DEG;
  const decl = Math.asin(Math.sin(23.439 * DEG) * Math.sin(lambda)) / DEG;
  const eotMin = 229.18 * (0.000075 + 0.001868 * Math.cos(g) - 0.032077 * Math.sin(g)
    - 0.014615 * Math.cos(2 * g) - 0.040849 * Math.sin(2 * g));
  const utcH = date.getUTCHours() + date.getUTCMinutes() / 60 + date.getUTCSeconds() / 3600;
  let slon = 180 - 15 * (utcH + eotMin / 60);
  slon = ((slon + 540) % 360) - 180;
  return [decl, slon];
}

function solarElevation(lat, lon, decl, slon) {
  return Math.asin(
    Math.sin(lat * DEG) * Math.sin(decl * DEG)
    + Math.cos(lat * DEG) * Math.cos(decl * DEG) * Math.cos((lon - slon) * DEG)) / DEG;
}

function latlonToGrid(lat, lon) {
  lon += 180; lat += 90;
  return String.fromCharCode(65 + Math.floor(lon / 20)) + String.fromCharCode(65 + Math.floor(lat / 10))
    + Math.floor((lon % 20) / 2) + Math.floor(lat % 10)
    + String.fromCharCode(97 + Math.floor((lon % 2) * 12)) + String.fromCharCode(97 + Math.floor((lat % 1) * 24));
}

const fmtMHz = hz => {
  const s = (hz / 1e6).toFixed(6);
  const [i, d] = s.split(".");
  return `${i}.${d.slice(0, 3)}.${d.slice(3)}`;
};

const WIDGETS = {

  prop: { title: "Propagation", icon: "📈", w: 470, h: 380, build(body) {
    body.append(h("div", { class: "spin" }, "loading…"));
    return { every: 900, refresh: async () => {
      try {
        const p = await api("/api/prop");
        body.replaceChildren(
          h("div", { class: "row" },
            kv("SFI", p.sfi), kv("A", p.a_index), kv("K", p.k_index),
            kv("Sunspots", p.sunspots), kv("MUF", p.muf)),
          h("div", { class: "small muted" },
            `${p.updated}${p.cached ? " · cached (offline)" : ""} · ${p.geomag}`),
          (() => {
            const tbl = h("table", { class: "grid" },
              h("tr", {}, h("th", {}, "Band"), h("th", {}, "Day"), h("th", {}, "Night")));
            for (const [name, tn] of Object.entries(p.bands || {}))
              tbl.append(h("tr", {}, h("td", {}, name), h("td", {}, tn.day || "?"), h("td", {}, tn.night || "?")));
            return tbl;
          })(),
          h("ul", { class: "small" }, ...p.advice.map(a => h("li", {}, a))));
      } catch (e) { body.replaceChildren(h("div", { class: "muted" }, "⚠ " + e.message)); }
    }};
  }},

  power: { title: "Power / Battery", icon: "🔋", w: 430, h: 360, build(body) {
    const volts = h("span", { class: "big" }, "--.-");
    const rows = h("div", { class: "row" });
    const lvl = h("span");
    const pi = h("div", { class: "small muted" });
    const wrap = h("div", { class: "chart-wrap" });
    const canvas = h("canvas", { class: "chart" });
    wrap.append(canvas);
    body.append(h("div", { class: "row" }, h("div", {}, volts, h("span", { class: "unit" }, " V "), lvl)),
      rows, pi, h("div", { class: "small muted" }, "Battery voltage — last hour"), wrap);
    const chart = lineChart(wrap, canvas, { xs: [], ys: [] }, {
      yUnit: " V", yFmt: v => v.toFixed(2),
      xLabel: t => new Date(t * 1000).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    });
    return { every: 30, refresh: async () => {
      try {
        const p = await api("/api/power");
        if (p.source === "none") {
          volts.textContent = "—";
          lvl.replaceChildren();
          rows.replaceChildren(h("div", { class: "muted small" }, p.hint));
        } else {
          volts.textContent = p.volts.toFixed(2);
          lvl.replaceChildren(badge(p.level));
          rows.replaceChildren(
            kv("Amps", p.amps.toFixed(2)), kv("Watts", p.watts.toFixed(1)),
            kv("Charge", p.soc + " %"), kv("Chemistry", p.chemistry));
        }
        pi.textContent = "Pi supply: " + p.pi;
        const hist = await api("/api/power/history?n=360");
        chart.data.xs = hist.t; chart.data.ys = hist.volts;
        chart.draw(-1);
      } catch (e) { pi.textContent = "⚠ " + e.message; }
    }};
  }},

  rig: { title: "Rig (CAT)", icon: "🎛", w: 430, h: 330, build(body) {
    const freq = h("div", { class: "big", id: "rig-freq" }, "—");
    const mode = h("span", { class: "muted" }, "");
    const msg = h("div", { class: "small muted" }, "");
    const finput = h("input", { type: "text", inputmode: "decimal", placeholder: "MHz e.g. 14.074" });
    let lastHz = null;
    const post = async payload => {
      try { await api("/api/rig", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) }); ctl.refresh(); }
      catch (e) { msg.textContent = "⚠ " + e.message; }
    };
    const step = d => lastHz !== null && post({ freq_hz: lastHz + d });
    body.append(freq, mode, msg,
      h("div", { class: "btnrow" },
        h("button", { class: "tbtn", onclick: () => step(-1000) }, "−1k"),
        h("button", { class: "tbtn", onclick: () => step(-100) }, "−100"),
        h("button", { class: "tbtn", onclick: () => step(100) }, "+100"),
        h("button", { class: "tbtn", onclick: () => step(1000) }, "+1k")),
      h("div", { class: "btnrow" },
        ...["USB", "LSB", "CW", "FM", "PKTUSB"].map(m =>
          h("button", { class: "tbtn", onclick: () => post({ mode: m }) }, m))),
      h("form", { class: "wform", onsubmit: e => {
          e.preventDefault();
          const mhz = parseFloat(finput.value);
          if (mhz > 0) post({ freq_hz: Math.round(mhz * 1e6) });
        } },
        finput, h("button", { class: "tbtn primary" }, "Set")),
      h("div", { class: "hint" }, "No TX control here on purpose — keying the radio stays a physical act."));
    const ctl = { every: 5, refresh: async () => {
      try {
        const r = await api("/api/rig");
        lastHz = r.freq_hz;
        freq.textContent = fmtMHz(r.freq_hz);
        mode.textContent = r.mode + (r.passband ? ` · ${r.passband} Hz` : "");
        msg.textContent = "";
      } catch (e) { freq.textContent = "—"; mode.textContent = ""; msg.textContent = "⚠ " + e.message; }
    }};
    return ctl;
  }},

  log: { title: "Logbook", icon: "📓", w: 560, h: 430, build(body) {
    const call = h("input", { placeholder: "Callsign*", autocapitalize: "characters" });
    const fq = h("input", { placeholder: "MHz", inputmode: "decimal" });
    const md = h("select", {}, ...["SSB", "FT8", "JS8", "CW", "FM", "PSK31", "RTTY", "AM"]
      .map(m => h("option", {}, m)));
    const rs = h("input", { value: "59", placeholder: "RST out" });
    const rr = h("input", { value: "59", placeholder: "RST in" });
    const nm = h("input", { placeholder: "Name" });
    const notes = h("input", { class: "full", placeholder: "Notes / QTH" });
    const msg = h("span", { class: "small muted" });
    const search = h("input", { type: "search", placeholder: "Search log…" });
    const list = h("div");
    const count = h("span", { class: "muted small" });

    async function refreshList() {
      const d = await api("/api/log?limit=30&q=" + encodeURIComponent(search.value.trim()));
      count.textContent = ` ${d.total} QSOs`;
      const tbl = h("table", { class: "grid" },
        h("tr", {}, h("th", {}, "UTC"), h("th", {}, "Call"), h("th", {}, "MHz"),
          h("th", {}, "Mode"), h("th", {}, "RST"), h("th", {}, "")));
      for (const q of d.qsos) {
        tbl.append(h("tr", {},
          h("td", { class: "small" }, (q.ts_utc || "").slice(5, 16)),
          h("td", {}, h("b", {}, q.call)),
          h("td", {}, q.freq_mhz ?? ""),
          h("td", {}, q.mode || ""),
          h("td", {}, `${q.rst_sent || ""}/${q.rst_rcvd || ""}`),
          h("td", {}, h("button", { class: "win-btn", title: "Delete", onclick: async () => {
            if (confirm(`Delete QSO with ${q.call}?`)) { await api("/api/log/" + q.id, { method: "DELETE" }); refreshList(); }
          } }, "🗑"))));
      }
      list.replaceChildren(tbl);
    }
    search.addEventListener("input", () => refreshList().catch(() => {}));

    // A tapped row in the Spots widget pre-fills the QSO entry form.
    document.addEventListener("hampi:pickcall", e => {
      const s = e.detail;
      call.value = s.call || "";
      if (s.grid) notes.value = (notes.value ? notes.value + " " : "") + s.grid;
      if (s.mode) {
        const m = s.mode === "~" ? "FT8" : s.mode;
        for (const o of md.options) if (o.value === m) md.value = m;
      }
      msg.textContent = `Filled from spot: ${s.call}`;
    });

    body.append(
      h("form", { class: "wform", onsubmit: async e => {
          e.preventDefault();
          if (!call.value.trim()) { msg.textContent = "Callsign required"; return; }
          try {
            if (!fq.value) {  // prefill from rig if it's connected
              try { fq.value = ((await api("/api/rig")).freq_hz / 1e6).toFixed(4); } catch (_) { /* no rig */ }
            }
            await api("/api/log", { method: "POST", headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ call: call.value, freq_mhz: fq.value || null, mode: md.value,
                rst_sent: rs.value, rst_rcvd: rr.value, name: nm.value, notes: notes.value }) });
            msg.textContent = `Logged ${call.value.toUpperCase()} ✓`;
            call.value = nm.value = notes.value = ""; rs.value = rr.value = "59";
            call.focus();
            refreshList();
          } catch (e2) { msg.textContent = "⚠ " + e2.message; }
        } },
        call, fq, md, rs, rr, nm, notes,
        h("button", { class: "tbtn primary" }, "Log it"), msg),
      h("div", { class: "row", style: "margin-top:10px; align-items:center" },
        search, count,
        h("a", { href: "/api/log/export.adi", class: "tbtn", style: "display:inline-flex;align-items:center;text-decoration:none" }, "⤓ ADIF")),
      list);
    return { every: 0, refresh: () => refreshList().catch(e => { count.textContent = "⚠ " + e.message; }) };
  }},

  wx: { title: "Weather", icon: "🌤", w: 430, h: 360, build(body) {
    body.append(h("div", { class: "spin" }, "loading…"));
    return { every: 900, refresh: async () => {
      try {
        const w = await api("/api/wx");
        const cur = w.data.current || {};
        const hourly = w.data.hourly || {};
        const rows = h("table", { class: "grid" },
          h("tr", {}, h("th", {}, "Hour"), h("th", {}, "°F"), h("th", {}, "Rain"), h("th", {}, "Gust")));
        (hourly.time || []).forEach((t, i) => {
          if (i % 3) return;
          rows.append(h("tr", {}, h("td", {}, t.slice(11, 16)),
            h("td", {}, hourly.temperature_2m[i]),
            h("td", {}, hourly.precipitation_probability[i] + "%"),
            h("td", {}, hourly.wind_gusts_10m[i])));
        });
        const gusts = (hourly.wind_gusts_10m || []).filter(Number.isFinite);
        const gmax = gusts.length ? Math.max(...gusts) : 0;
        body.replaceChildren(
          h("div", { class: "row" },
            h("div", {}, h("span", { class: "big" }, Math.round(cur.temperature_2m ?? 0)),
              h("span", { class: "unit" }, " °F · " + (w.wmo[cur.weather_code] || ""))),
          ),
          h("div", { class: "row" },
            kv("Wind", `${cur.wind_speed_10m} mph`), kv("Gust", `${cur.wind_gusts_10m}`),
            kv("Humidity", `${cur.relative_humidity_2m}%`), kv("Pressure", `${cur.pressure_msl}`)),
          gmax >= 25 ? h("div", { class: "small", style: "color:var(--warn)" },
            `⚠ Gusts to ${Math.round(gmax)} mph expected — guy your masts.`) : null,
          h("div", { class: "small muted" }, `${w.lat.toFixed(3)}, ${w.lon.toFixed(3)} via ${w.source}${w.cached ? " · cached" : ""}`),
          rows);
      } catch (e) { body.replaceChildren(h("div", { class: "muted" }, "⚠ " + e.message)); }
    }};
  }},

  gps: { title: "GPS / Time", icon: "🛰", w: 380, h: 260, build(body) {
    body.append(h("div", { class: "spin" }, "loading…"));
    return { every: 20, refresh: async () => {
      try {
        const s = await api("/api/status");
        const g = s.gps || {};
        const fix = g.state === "fix";
        body.replaceChildren(
          h("div", { class: "row" },
            h("div", {}, fix ? badge("OK") : h("span", { class: "badge warn" }, "no fix"),
              " ", h("b", {}, fix ? `${g.mode}D fix` : (g.state === "no-gpsd" ? "gpsd not running" : "searching…")))),
          fix ? h("div", { class: "row" },
            kv("Lat", g.lat.toFixed(5)), kv("Lon", g.lon.toFixed(5)),
            kv("Grid", latlonToGrid(g.lat, g.lon)),
            kv("Alt", g.alt !== undefined ? Math.round(g.alt) + " m" : "—")) : null,
          h("div", { class: "row" },
            kv("Clock sync", s.time_synced === true ? "✓ yes" : s.time_synced === false ? "✗ NO" : "?"),
            kv("UTC", s.utc.slice(11))),
          h("div", { class: "hint" }, "FT8/JS8 need the clock within ~1 s. A USB GPS keeps it synced with no internet."));
      } catch (e) { body.replaceChildren(h("div", { class: "muted" }, "⚠ " + e.message)); }
    }};
  }},

  antenna: { title: "Antenna Calc", icon: "📏", w: 520, h: 420, build(body) {
    const fi = h("input", { placeholder: "MHz or band (40m)", inputmode: "decimal" });
    const ty = h("select", {}, h("option", { value: "" }, "All types"),
      ...[["dipole", "Dipole"], ["invv", "Inverted-V"], ["efhw", "End-fed half wave"],
          ["vertical", "¼-wave vertical"], ["nvis", "NVIS"], ["jpole", "J-pole"],
          ["random", "Random wire"], ["choke", "Feedline choke"]]
        .map(([v, t]) => h("option", { value: v }, t)));
    const out = preBox();
    body.append(h("form", { class: "wform", onsubmit: async e => {
        e.preventDefault();
        try {
          const d = await api(`/api/antenna?freq=${encodeURIComponent(fi.value)}&type=${ty.value}`);
          out.textContent = d.text;
        } catch (e2) { out.textContent = "⚠ " + e2.message; }
      } },
      fi, ty, h("button", { class: "tbtn primary" }, "Cut chart")),
      h("div", { class: "btnrow" },
        ...["80m", "40m", "20m", "17m", "15m", "10m", "2m"].map(b =>
          h("button", { class: "tbtn", onclick: () => { fi.value = b; fi.form.requestSubmit(); } }, b))),
      out);
    return {};
  }},

  heading: { title: "Beam Heading", icon: "🧭", w: 440, h: 300, build(body) {
    const to = h("input", { placeholder: "Target grid (JO01)", autocapitalize: "characters" });
    const from = h("input", { placeholder: "From (blank = station)" , autocapitalize: "characters"});
    const out = preBox();
    body.append(h("form", { class: "wform", onsubmit: async e => {
        e.preventDefault();
        try {
          const d = await api(`/api/heading?to=${encodeURIComponent(to.value)}&from=${encodeURIComponent(from.value)}`);
          out.textContent = d.text;
        } catch (e2) { out.textContent = "⚠ " + e2.message; }
      } },
      to, from, h("button", { class: "tbtn primary" }, "Heading")), out);
    return {};
  }},

  scan: { title: "Spectrum Scan", icon: "📶", w: 520, h: 400, build(body) {
    const preset = h("select", {},
      h("option", { value: "144M:148M" }, "2 m (144–148)"),
      h("option", { value: "420M:450M" }, "70 cm (420–450)"),
      h("option", { value: "118M:137M" }, "Airband"),
      h("option", { value: "88M:108M" }, "FM broadcast (sanity check)"));
    const status = h("span", { class: "small muted" }, "SDR dongle required");
    const wrap = h("div", { class: "chart-wrap" });
    const canvas = h("canvas", { class: "chart", style: "height:170px" });
    wrap.append(canvas);
    const topList = h("div", { class: "small" });
    const chart = lineChart(wrap, canvas, { xs: [], ys: [] }, {
      yUnit: " dB", yFmt: v => v.toFixed(0),
      xLabel: f => f.toFixed(3) + " MHz",
    });
    body.append(h("div", { class: "wform" }, preset,
      h("button", { class: "tbtn primary", onclick: async e => {
        e.target.disabled = true;
        status.textContent = "sweeping (~15 s)…"; status.className = "small spin";
        try {
          const d = await api(`/api/scan?range=${preset.value}&secs=12`);
          chart.data.xs = d.freqs; chart.data.ys = d.db; chart.draw(-1);
          status.textContent = `${d.range} · strongest:`; status.className = "small muted";
          topList.replaceChildren(...d.top.slice(0, 6).map(([f, db]) =>
            h("span", { class: "chip", style: "margin:2px" }, `${f.toFixed(3)} MHz ${db.toFixed(0)} dB`)));
        } catch (e2) { status.textContent = "⚠ " + e2.message; status.className = "small muted"; }
        e.target.disabled = false;
      } }, "▶ Sweep")),
      status, wrap, topList);
    return {};
  }},

  spots: { title: "FT8/JS8 Spots", icon: "📻", w: 620, h: 430, build(body) {
    let lastSeq = 0, cqOnly = false;
    const rows = [];            // newest first, capped
    const head = h("div", { class: "row", style: "align-items:center" });
    const state = h("div", { class: "small muted" }, "Waiting for WSJT-X / JS8Call…");
    const btnAll = h("button", { class: "tbtn active", onclick: () => setFilter(false) }, "All");
    const btnCq = h("button", { class: "tbtn", onclick: () => setFilter(true) }, "CQ only");
    const tblWrap = h("div");
    function setFilter(v) {
      cqOnly = v;
      btnAll.classList.toggle("active", !v);
      btnCq.classList.toggle("active", v);
      render();
    }
    function render() {
      const tbl = h("table", { class: "grid" },
        h("tr", {}, h("th", {}, "UTC"), h("th", {}, "dB"), h("th", {}, "Call"),
          h("th", {}, "Grid"), h("th", {}, "km"), h("th", {}, "°"), h("th", {}, "Message")));
      let shown = 0;
      for (const s of rows) {
        if (cqOnly && !s.cq) continue;
        if (++shown > 60) break;
        const tr = h("tr", { style: s.cq ? "box-shadow: inset 3px 0 var(--accent)" : "" },
          h("td", { class: "small" }, s.utc),
          h("td", {}, s.snr > 0 ? "+" + s.snr : String(s.snr)),
          h("td", {}, h("b", {}, s.call || "—")),
          h("td", {}, s.grid || ""),
          h("td", {}, s.km ?? ""),
          h("td", {}, s.az ?? ""),
          h("td", { class: "small" }, s.msg));
        if (s.call) {
          tr.style.cursor = "pointer";
          tr.title = "Tap to fill the Logbook widget";
          tr.addEventListener("click", () => document.dispatchEvent(
            new CustomEvent("hampi:pickcall", { detail: s })));
        }
        tbl.append(tr);
      }
      if (!shown) tbl.append(h("tr", {}, h("td", { colspan: "7", class: "muted small" },
        "No decodes yet. In WSJT-X: Settings → Reporting → UDP Server 127.0.0.1:2237 (the default). " +
        "In JS8Call: Settings → Reporting → Enable UDP API (port 2242).")));
      tblWrap.replaceChildren(tbl);
    }
    head.append(btnAll, btnCq, state);
    body.append(head, tblWrap);
    render();
    return { every: 5, refresh: async () => {
      try {
        const d = await api("/api/spots?since=" + lastSeq);
        for (const s of d.spots) { lastSeq = Math.max(lastSeq, s.seq); rows.unshift(s); }
        rows.length = Math.min(rows.length, 200);
        const st = d.status || {};
        const bits = [];
        if (st.dial_hz) bits.push(`${st.band} · ${fmtMHz(st.dial_hz)} ${st.mode || ""}`);
        for (const [name, li] of Object.entries(d.listeners || {})) {
          if (li.error) bits.push(`${name}: ⚠ ${li.error}`);
          else if (li.age_s !== null) bits.push(`${name} ✓ ${li.age_s}s ago`);
        }
        bits.push(`${d.unique_calls} unique calls`);
        if (!d.my_grid) bits.push("set GRID in station.conf for distance/bearing");
        state.textContent = bits.join(" · ");
        if (d.spots.length) render();
      } catch (e) { state.textContent = "⚠ " + e.message; }
    }};
  }},

  map: { title: "Grayline Map", icon: "🌍", w: 560, h: 600, build(body) {
    body.classList.add("map-body");
    const wrap = h("div", { class: "map-wrap" });
    const canvas = h("canvas", { class: "map" });
    const tip = h("div", { class: "tooltip", hidden: "" });
    wrap.append(canvas, tip);
    const state = h("span", { class: "muted" }, "loading…");
    let showSpots = true, showLog = true;
    const tSpots = h("button", { class: "tbtn active", style: "font-size:13px",
      onclick: () => { showSpots = !showSpots; tSpots.classList.toggle("active"); draw(); } }, "Spots");
    const tLog = h("button", { class: "tbtn active", style: "font-size:13px",
      onclick: () => { showLog = !showLog; tLog.classList.toggle("active"); draw(); } }, "Log");
    const legend = h("div", { class: "map-legend" }, tSpots, tLog,
      h("span", {}, "● CQ  ○ heard"), h("span", {}, "◆ logged QSO"),
      h("span", {}, "☀ sun · shaded = night, warm band = grayline"), state);
    body.append(wrap, legend);

    let world = null, center = null, centerLabel = "";
    let contacts = [];       // {lat,lon,call,grid,cq,src,ts,km,az,msg}
    let sinceSeq = 0;
    const ctx = canvas.getContext("2d");

    fetch("world.json").then(r => r.json()).then(w => { world = w; draw(); })
      .catch(() => { state.textContent = "⚠ world.json missing"; });

    const project = (lat, lon, R) => {
      const p1 = center[0] * DEG, p2 = lat * DEG, dl = (lon - center[1]) * DEG;
      const c = Math.acos(Math.max(-1, Math.min(1,
        Math.sin(p1) * Math.sin(p2) + Math.cos(p1) * Math.cos(p2) * Math.cos(dl))));
      const az = Math.atan2(Math.sin(dl) * Math.cos(p2),
        Math.cos(p1) * Math.sin(p2) - Math.sin(p1) * Math.cos(p2) * Math.cos(dl));
      const r = c / Math.PI * R;
      return [R + r * Math.sin(az), R - r * Math.cos(az)];
    };
    const inverse = (x, y, R) => {
      const dx = x - R, dy = R - y, r = Math.hypot(dx, dy);
      if (r > R) return null;
      const c = r / R * Math.PI, az = Math.atan2(dx, dy), p1 = center[0] * DEG;
      const lat = Math.asin(Math.sin(p1) * Math.cos(c) + Math.cos(p1) * Math.sin(c) * Math.cos(az));
      const lon = center[1] + Math.atan2(Math.sin(az) * Math.sin(c) * Math.cos(p1),
        Math.cos(c) - Math.sin(p1) * Math.sin(lat)) / DEG;
      return [lat / DEG, ((lon + 540) % 360) - 180];
    };

    function polyline(pts, R) {
      // One path, with pen-lifts at projection-edge jumps (antipodal wraps).
      let lastX = null, lastY = null;
      ctx.beginPath();
      for (const [lat, lon] of pts) {
        const [x, y] = project(lat, lon, R);
        if (lastX !== null && (x - lastX) ** 2 + (y - lastY) ** 2 < R * R * 0.25)
          ctx.lineTo(x, y);
        else
          ctx.moveTo(x, y);
        lastX = x; lastY = y;
      }
      ctx.stroke();
    }

    function draw() {
      if (!center) return;
      const dpr = devicePixelRatio || 1;
      const size = Math.min(wrap.clientWidth, wrap.clientHeight);
      if (size < 60) return;
      canvas.width = wrap.clientWidth * dpr; canvas.height = wrap.clientHeight * dpr;
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      ctx.clearRect(0, 0, wrap.clientWidth, wrap.clientHeight);
      const R = size / 2 - 12;
      ctx.save();
      ctx.translate((wrap.clientWidth - size) / 2 + 12, (wrap.clientHeight - size) / 2 + 12);

      // Globe disk + clip
      ctx.beginPath(); ctx.arc(R, R, R, 0, 7);
      ctx.fillStyle = cssVar("--surface"); ctx.fill();
      ctx.strokeStyle = cssVar("--border"); ctx.lineWidth = 1.5; ctx.stroke();
      ctx.save();
      ctx.beginPath(); ctx.arc(R, R, R, 0, 7); ctx.clip();

      // Night + grayline shading (sampled cells via inverse projection)
      const [decl, slon] = subsolarPoint(new Date());
      const cell = Math.max(4, size / 90);
      const night = "rgba(0,0,0,0.42)";
      const gray = document.body.classList.contains("night")
        ? "rgba(255,90,90,0.14)" : "rgba(201,133,0,0.20)";
      for (let y = 0; y < 2 * R; y += cell) {
        for (let x = 0; x < 2 * R; x += cell) {
          const ll = inverse(x + cell / 2, y + cell / 2, R);
          if (!ll) continue;
          const elev = solarElevation(ll[0], ll[1], decl, slon);
          if (elev < -8) { ctx.fillStyle = night; ctx.fillRect(x, y, cell + 1, cell + 1); }
          else if (elev < 8) { ctx.fillStyle = gray; ctx.fillRect(x, y, cell + 1, cell + 1); }
        }
      }

      // Graticule
      ctx.strokeStyle = cssVar("--border"); ctx.lineWidth = 0.6;
      for (let lon = -180; lon < 180; lon += 30) {
        const pts = []; for (let lat = -88; lat <= 88; lat += 4) pts.push([lat, lon]);
        polyline(pts, R);
      }
      for (let lat = -60; lat <= 60; lat += 30) {
        const pts = []; for (let lon = -180; lon <= 180; lon += 4) pts.push([lat, lon]);
        polyline(pts, R);
      }

      // Coastlines
      if (world) {
        ctx.strokeStyle = cssVar("--text-2"); ctx.lineWidth = 1; ctx.globalAlpha = 0.9;
        for (const line of world.lines) {
          const pts = [];
          for (let i = 0; i < line.length; i += 2) pts.push([line[i], line[i + 1]]);
          polyline(pts, R);
        }
        ctx.globalAlpha = 1;
      }

      // Distance rings
      ctx.strokeStyle = cssVar("--border"); ctx.fillStyle = cssVar("--text-2");
      ctx.lineWidth = 0.8; ctx.font = "10px system-ui"; ctx.setLineDash([4, 4]);
      for (const km of [5000, 10000, 15000]) {
        const r = km / 6371 / Math.PI * R;
        ctx.beginPath(); ctx.arc(R, R, r, 0, 7); ctx.stroke();
        ctx.fillText(`${km / 1000}k km`, R + 3, R - r + 11);
      }
      ctx.setLineDash([]);

      // Contacts: straight line from center = the actual great-circle path
      const accent = cssVar("--chart"), logCol = cssVar("--logmark");
      const now = Date.now() / 1000;
      for (const c of contacts) c.xy = project(c.lat, c.lon, R);
      const visible = contacts.filter(c => (c.src === "log" ? showLog : showSpots));
      for (const c of visible.slice(-25)) {
        ctx.strokeStyle = c.src === "log" ? logCol : accent;
        ctx.globalAlpha = c.src === "log" ? 0.4 : Math.max(0.15, 1 - (now - c.ts) / 1800) * 0.6;
        ctx.lineWidth = 1.4;
        ctx.beginPath(); ctx.moveTo(R, R); ctx.lineTo(c.xy[0], c.xy[1]); ctx.stroke();
      }
      ctx.globalAlpha = 1;
      for (const c of visible) {
        const [x, y] = c.xy;
        ctx.strokeStyle = cssVar("--surface"); ctx.lineWidth = 2;
        if (c.src === "log") {
          ctx.fillStyle = logCol;
          ctx.beginPath(); ctx.moveTo(x, y - 5); ctx.lineTo(x + 5, y);
          ctx.lineTo(x, y + 5); ctx.lineTo(x - 5, y); ctx.closePath();
          ctx.fill(); ctx.stroke();
        } else if (c.cq) {
          ctx.fillStyle = accent;
          ctx.beginPath(); ctx.arc(x, y, 4.5, 0, 7); ctx.fill(); ctx.stroke();
        } else {
          ctx.strokeStyle = accent; ctx.lineWidth = 1.6;
          ctx.beginPath(); ctx.arc(x, y, 3.5, 0, 7); ctx.stroke();
        }
      }

      // Sun + station
      const [sx, sy] = project(decl, slon, R);
      ctx.fillStyle = cssVar("--warn");
      ctx.beginPath(); ctx.arc(sx, sy, 6, 0, 7); ctx.fill();
      ctx.strokeStyle = cssVar("--surface"); ctx.lineWidth = 2; ctx.stroke();
      ctx.fillStyle = cssVar("--accent");   // station marker in brand purple
      ctx.beginPath(); ctx.arc(R, R, 5, 0, 7); ctx.fill();
      ctx.strokeStyle = cssVar("--surface"); ctx.stroke();
      ctx.restore();

      // Cardinal labels (bearing = screen angle: the point of this projection)
      ctx.fillStyle = cssVar("--text-2"); ctx.font = "12px system-ui";
      ctx.textAlign = "center";
      ctx.fillText("N 0°", R, 10); ctx.fillText("S 180°", R, 2 * R + 10);
      ctx.textAlign = "left"; ctx.fillText("W 270°", 2, R + 4);
      ctx.textAlign = "right"; ctx.fillText("E 90°", 2 * R - 2, R + 4);
      ctx.textAlign = "left";
      ctx.restore();
    }

    canvas.addEventListener("pointerdown", e => {
      const r = canvas.getBoundingClientRect();
      const size = Math.min(wrap.clientWidth, wrap.clientHeight);
      const ox = (wrap.clientWidth - size) / 2 + 12, oy = (wrap.clientHeight - size) / 2 + 12;
      const px = e.clientX - r.left - ox, py = e.clientY - r.top - oy;
      let best = null, bd = 26 * 26;
      for (const c of contacts) {
        if (!c.xy || (c.src === "log" ? !showLog : !showSpots)) continue;
        const d = (c.xy[0] - px) ** 2 + (c.xy[1] - py) ** 2;
        if (d < bd) { bd = d; best = c; }
      }
      if (best) {
        tip.hidden = false;
        const age = Math.round((Date.now() / 1000 - best.ts) / 60);
        tip.textContent = `${best.call || "?"} · ${best.grid} · ${best.km} km @ ${best.az}° · `
          + (best.src === "log" ? "logged" : `${age} min ago`);
        tip.style.left = (best.xy[0] + ox) + "px"; tip.style.top = (best.xy[1] + oy) + "px";
      } else tip.hidden = true;
    });

    function addContact(lat, lon, extra) {
      const [az, km] = greatCircle(center[0], center[1], lat, lon);
      contacts.push(Object.assign({ lat, lon, az, km, xy: [0, 0] }, extra));
      if (contacts.length > 300) contacts.splice(0, contacts.length - 300);
    }

    async function refresh() {
      try {
        const st = await api("/api/status");
        const sp = await api("/api/spots?since=" + sinceSeq);
        if (!center) {
          if (st.gps && st.gps.state === "fix") { center = [st.gps.lat, st.gps.lon]; centerLabel = "GPS"; }
          else if (sp.my_grid) { center = gridToLatlon(sp.my_grid); centerLabel = sp.my_grid; }
          if (!center) { state.textContent = "Set GRID in /etc/hampi/station.conf (or plug in GPS)"; return; }
          state.textContent = "centered on " + centerLabel;
          // Seed history: logged QSOs with grids
          try {
            const lg = await api("/api/log?limit=50");
            for (const q of lg.qsos) {
              const ll = q.grid && gridToLatlon(q.grid);
              if (ll) addContact(ll[0], ll[1],
                { call: q.call, grid: q.grid, src: "log", cq: false,
                  ts: Date.parse((q.ts_utc || "") + "Z") / 1000 || Date.now() / 1000 });
            }
          } catch (e) { /* log empty */ }
        }
        for (const s of sp.spots) {
          sinceSeq = Math.max(sinceSeq, s.seq);
          const ll = s.grid && gridToLatlon(s.grid);
          if (ll) addContact(ll[0], ll[1],
            { call: s.call, grid: s.grid, src: s.src, cq: s.cq, ts: s.ts, msg: s.msg });
        }
        draw();
      } catch (e) { state.textContent = "⚠ " + e.message; }
    }

    new ResizeObserver(() => draw()).observe(wrap);
    const sunTimer = setInterval(() => {   // terminator creeps ~0.25 deg/min
      if (!document.contains(canvas)) { clearInterval(sunTimer); return; }
      draw();
    }, 60000);
    return { every: 10, refresh };
  }},

  sys: { title: "System", icon: "🖥", w: 380, h: 280, build(body) {
    body.append(h("div", { class: "spin" }, "loading…"));
    return { every: 30, refresh: async () => {
      try {
        const s = await api("/api/status");
        body.replaceChildren(
          h("div", { class: "row" },
            kv("CPU temp", s.cpu_temp_c !== null ? s.cpu_temp_c.toFixed(0) + " °C" : "—"),
            kv("Disk free", s.disk_free_gb + " GB"),
            kv("Uptime", s.uptime_s ? (s.uptime_s / 3600).toFixed(1) + " h" : "—")),
          h("div", { class: "small" }, h("b", {}, "Phone access: "),
            ...(s.ips.length ? s.ips.map(ip => h("span", { class: "chip", style: "margin:2px" }, `http://${ip}:8073`))
              : ["no network — run: hampi-hotspot up"])),
          h("div", { class: "small muted" },
            s.physical_keyboard ? "⌨ Physical keyboard: " + s.keyboards.join(", ") : "⌨ No physical keyboard — touch keyboard active"),
          h("div", { class: "small muted" },
            s.license && s.license.state === "licensed"
              ? `📜 Licensed to ${s.license.call}${s.license.name ? " (" + s.license.name + ")" : ""} — lifetime`
              : s.license && s.license.state === "trial"
                ? `📜 RF π trial — ${s.license.days_left} days left`
                : s.license && s.license.state === "dev" ? "📜 Unlicensed build (no enforcement)" : null),
          h("div", { class: "hint" },
            `Host ${s.hostname} · RF π suite is licensed software; the bundled ` +
            `open-source apps are free — see /etc/hampi/OPEN-SOURCE.txt`));
      } catch (e) { body.replaceChildren(h("div", { class: "muted" }, "⚠ " + e.message)); }
    }};
  }},
};

/* ---------------- Launcher ---------------- */

function renderLauncherGrid() {
  const grid = $("#launcher-grid");
  grid.replaceChildren(...Object.entries(WIDGETS).map(([id, w]) =>
    h("button", { class: "launch-btn" + (openWins.has(id) ? " open" : ""),
      onclick: () => { openWins.has(id) ? closeWidget(id) : openWidget(id); renderLauncherGrid(); } },
      h("span", { class: "ico" }, w.icon), h("span", {}, w.title))));
}
$("#btn-widgets").addEventListener("click", () => { renderLauncherGrid(); $("#launcher").hidden = false; });
$("#launcher-close").addEventListener("click", () => { $("#launcher").hidden = true; });
$("#launcher").addEventListener("click", e => { if (e.target.id === "launcher") $("#launcher").hidden = true; });

/* ---------------- Top bar: clock, status chips, night/fullscreen ---------------- */

setInterval(() => {
  $("#clock-utc").textContent = new Date().toISOString().slice(11, 19);
}, 1000);

let physicalKB = false;   // server- or locally-detected hardware keyboard

async function pollStatus() {
  try {
    const s = await api("/api/status");
    applyLicense(s.license);
    const bc = $("#brand-call");
    if (s.callsign && s.callsign !== "N0CALL") { bc.textContent = s.callsign; bc.hidden = false; }
    const gps = $("#chip-gps"), sync = $("#chip-sync"), kb = $("#chip-kb");
    const fix = s.gps && s.gps.state === "fix";
    gps.textContent = fix ? "GPS ✓" : "GPS —";
    gps.className = "chip " + (fix ? "ok" : "warn");
    sync.textContent = s.time_synced ? "SYNC ✓" : "SYNC ✗";
    sync.className = "chip " + (s.time_synced ? "ok" : "bad");
    if (s.physical_keyboard) physicalKB = true;
    else if (!localKeySeen) physicalKB = false;   // unplugged -> touch again
    kb.textContent = physicalKB ? "KB ⌨" : "KB 👆";
    kb.className = "chip " + (physicalKB ? "ok" : "");
    kb.title = physicalKB ? "Physical keyboard active (overrides touch keyboard): " + s.keyboards.join(", ")
                          : "Touch keyboard mode";
    if (physicalKB) hideOSK();
  } catch (e) { /* server restarting */ }
  try {
    const p = await api("/api/power");
    const chip = $("#chip-batt");
    if (p.source === "none") { chip.textContent = "BATT —"; chip.className = "chip"; }
    else {
      chip.textContent = `BATT ${p.volts.toFixed(1)}V ${Math.round(p.soc)}%`;
      chip.className = "chip " + (p.level === "OK" ? "ok" : p.level === "WARN" ? "warn" : "bad");
    }
  } catch (e) { /* no power endpoint yet */ }
}

$("#btn-night").addEventListener("click", () => {
  layout.night = !layout.night;
  document.body.classList.toggle("night", layout.night);
  saveLayout();
  for (const entry of openWins.values()) entry.refresh();
});
$("#btn-full").addEventListener("click", () => {
  document.fullscreenElement ? document.exitFullscreen() : document.documentElement.requestFullscreen();
});

/* ---------------- License: trial chip + lock screen ---------------- */

let licenseState = null;
let lockAutoShown = false;   // lock opened by expiry, not by the user tapping the chip

function applyLicense(lic) {
  const chips = $("#chips");
  let chip = $("#chip-trial");
  if (lic && lic.state === "trial") {
    if (!chip) {
      chip = h("span", { class: "chip warn", id: "chip-trial",
        title: "RF π trial - tap to enter a license key",
        onclick: () => showLock(lic, true) });
      chips.prepend(chip);
    }
    chip.textContent = `TRIAL ${lic.days_left}d`;
  } else if (chip) chip.remove();

  if (lic && lic.state === "expired") {
    showLock(lic, false);
  } else if (lockAutoShown) {
    // Was locked, now isn't (freshly activated, or a stale-cache flash on
    // load): drop the lock without waiting on anything.
    $("#lock").hidden = true;
    lockAutoShown = false;
    if (licenseState === "expired") location.reload();  // re-enable widget timers
  }
  licenseState = lic ? lic.state : null;
}

function showLock(lic, dismissable) {
  const lock = $("#lock");
  lock.hidden = false;
  if (!dismissable) lockAutoShown = true;
  $("#lock-title").textContent = dismissable
    ? `RF π trial — ${lic.days_left} day${lic.days_left === 1 ? "" : "s"} left`
    : "RF π trial expired";
  const buy = $("#lock-buy");
  if (lic.purchase_url) {
    buy.hidden = false;
    buy.replaceChildren("Get a lifetime license at ",
      h("a", { href: lic.purchase_url, target: "_blank" }, lic.purchase_url));
  } else buy.hidden = true;
  lock.onclick = dismissable ? (e => { if (e.target === lock) lock.hidden = true; }) : null;
}

$("#lock-activate").addEventListener("click", async () => {
  const msg = $("#lock-msg");
  msg.textContent = "";
  try {
    const r = await api("/api/license", { method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ key: $("#lock-key").value }) });
    msg.style.color = "var(--good)";
    msg.textContent = `Licensed to ${r.call}${r.name ? " (" + r.name + ")" : ""} — thank you & 73!`;
    setTimeout(() => location.reload(), 1500);
  } catch (e) {
    msg.style.color = "var(--crit)";
    msg.textContent = e.message;
  }
});
$("#lock-export").addEventListener("click", () => { location.href = "/api/log/export.adi"; });

/* ---------------- On-screen keyboard ---------------- */

const osk = $("#osk");
let oskTarget = null;
let localKeySeen = false;
let kbMode = layout.kbMode || "auto";   // auto | on | off

const OSK_LETTERS = [
  ["1", "2", "3", "4", "5", "6", "7", "8", "9", "0"],
  ["q", "w", "e", "r", "t", "y", "u", "i", "o", "p"],
  ["a", "s", "d", "f", "g", "h", "j", "k", "l"],
  ["⇧", "z", "x", "c", "v", "b", "n", "m", "⌫"],
  ["?123", ",", "space", ".", "/", "↵", "▼"],
];
const OSK_SYMBOLS = [
  ["1", "2", "3", "4", "5", "6", "7", "8", "9", "0"],
  ["!", "@", "#", "$", "%", "&", "*", "(", ")"],
  ["-", "_", "+", "=", ":", ";", "'", "\"", "⌫"],
  ["ABC", ",", "space", ".", "/", "↵", "▼"],
];
let oskShift = true;   // callsigns are uppercase; start shifted
let oskSymbols = false;

function buildOSK() {
  osk.replaceChildren(...(oskSymbols ? OSK_SYMBOLS : OSK_LETTERS).map(row =>
    h("div", { class: "osk-row" }, ...row.map(key => {
      const wide = ["⇧", "⌫", "?123", "ABC", "↵", "▼"].includes(key);
      const label = key === "space" ? " " :
        (key.length === 1 && !oskSymbols && oskShift ? key.toUpperCase() : key);
      const b = h("button", { class: "osk-key" + (key === "space" ? " space" : wide ? " wide" : "") },
        key === "space" ? "␣" : label);
      b.addEventListener("pointerdown", e => {
        e.preventDefault();   // keep focus in the input
        oskPress(key);
      });
      return b;
    }))));
}

function oskPress(key) {
  const t = oskTarget;
  if (key === "▼") { hideOSK(); if (t) t.blur(); return; }
  if (key === "⇧") { oskShift = !oskShift; buildOSK(); return; }
  if (key === "?123") { oskSymbols = true; buildOSK(); return; }
  if (key === "ABC") { oskSymbols = false; buildOSK(); return; }
  if (!t) return;
  if (key === "⌫") {
    const { selectionStart: s, selectionEnd: e } = t;
    if (s === e && s > 0) t.setRangeText("", s - 1, e, "end");
    else t.setRangeText("", s, e, "end");
  } else if (key === "↵") {
    if (t.form) t.form.requestSubmit();
    else t.blur();
    return;
  } else {
    let ch = key === "space" ? " " : key;
    if (!oskSymbols && oskShift && ch.length === 1) ch = ch.toUpperCase();
    t.setRangeText(ch, t.selectionStart, t.selectionEnd, "end");
  }
  t.dispatchEvent(new Event("input", { bubbles: true }));
}

function showOSK() {
  if (kbMode === "off") return;
  if (kbMode === "auto" && physicalKB) return;   // hardware keyboard overrides
  buildOSK();
  osk.hidden = false;
  document.body.classList.add("osk-open");
}
function hideOSK() {
  osk.hidden = true;
  document.body.classList.remove("osk-open");
}

document.addEventListener("focusin", e => {
  const el = e.target;
  if (el.matches("input:not([type=checkbox]):not([type=radio]), textarea")) {
    oskTarget = el;
    showOSK();
  }
});
document.addEventListener("focusout", () => {
  setTimeout(() => {
    const a = document.activeElement;
    if (!a || !a.matches("input, textarea")) hideOSK();
  }, 120);
});

// Any genuine hardware keypress = a physical keyboard is in use. It wins.
document.addEventListener("keydown", e => {
  if (!e.isTrusted) return;
  localKeySeen = true;
  physicalKB = true;
  hideOSK();
  $("#chip-kb").textContent = "KB ⌨";
  $("#chip-kb").className = "chip ok";
});

$("#btn-kbtoggle").addEventListener("click", () => {
  kbMode = kbMode === "auto" ? "on" : kbMode === "on" ? "off" : "auto";
  layout.kbMode = kbMode;
  saveLayout();
  const b = $("#btn-kbtoggle");
  b.classList.toggle("active", kbMode !== "auto");
  b.title = { auto: "Keyboard: auto (touch unless a real keyboard is attached)",
              on: "Keyboard: always show on-screen keys",
              off: "Keyboard: never show on-screen keys" }[kbMode];
  if (kbMode === "off") hideOSK();
  if (kbMode === "on" && oskTarget && document.activeElement === oskTarget) showOSK();
});

/* ---------------- Boot ---------------- */

document.body.classList.toggle("night", !!layout.night);
applyStackMode();
// Deep links: ?open=spots,rig force-opens widgets; add &solo=1 to show ONLY
// those (single-widget kiosk displays) without touching the saved layout.
const bootQS = new URLSearchParams(location.search);
const bootForced = (bootQS.get("open") || "").split(",").filter(id => WIDGETS[id]);
if (!(bootQS.has("solo") && bootForced.length))
  for (const id of layout.open.slice()) openWidget(id);
for (const id of bootForced) openWidget(id);
if (!openWins.size) openWidget("sys");
pollStatus();
setInterval(pollStatus, 10000);
