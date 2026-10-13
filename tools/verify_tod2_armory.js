// verify_tod2_armory.js — prove docs/tod2_armory.html (the published Armory artifact) RUNS.
// 2026-09-28: a bracket slip in a data row broke the whole page ("Is the armory artifact
// broken?") and verify_armory_render.js only covers docs/armory.html. This runs the page's
// script under a small DOM mock and fails on any exception or an empty tab.
//   node tools/verify_tod2_armory.js
const fs = require('fs'), vm = require('vm'), assert = require('assert');
const html = fs.readFileSync('docs/tod2_armory.html', 'utf8');
const scripts = [...html.matchAll(/<script>([\s\S]*?)<\/script>/g)].map(m => m[1]);
assert(scripts.length, 'no inline script');

function el(id, attrs = {}) {
  const e = { id, attrs: { ...attrs }, children: [], hidden: false, _html: '', listeners: {},
    dataset: attrs['data-tab'] ? { tab: attrs['data-tab'] } : {},
    setAttribute(k, v) { this.attrs[k] = String(v); }, getAttribute(k) { return this.attrs[k] ?? null; },
    addEventListener(t, f) { this.listeners[t] = f; },
    closest() { return null; },
    get innerHTML() { return this._html; },
    set innerHTML(v) {
      this._html = String(v);
      // rebuild the children a caller might walk (nav buttons, filter chips)
      this.children = [...this._html.matchAll(/<button([^>]*)>/g)].map(m => {
        const a = {}; for (const x of m[1].matchAll(/([\w-]+)="([^"]*)"/g)) a[x[1]] = x[2];
        const b = el(a.id || '', a); b.dataset = { f: a['data-f'] }; return b;
      });
    },
    set onclick(f) { this.listeners.click = f; },
  };
  return e;
}
const ids = {};
for (const m of html.matchAll(/<(section|nav|div)[^>]*\bid="([\w-]+)"([^>]*)>/g)) {
  const a = {}; for (const x of m[0].matchAll(/([\w-]+)="([^"]*)"/g)) a[x[1]] = x[2];
  ids[m[2]] = el(m[2], a);
}
const document = {
  querySelector(sel) {
    if (sel.startsWith('#')) { const k = sel.slice(1); return ids[k] || (ids[k] = el(k)); }
    return null;
  },
  querySelectorAll(sel) {
    if (sel === 'section[data-tab]') return Object.values(ids).filter(e => e.dataset.tab);
    return [];
  },
};
const ctx = { document, localStorage: { getItem: () => null, setItem() {} }, location: { hash: '' },
  history: { replaceState() {} }, console, Math, String, Number, Object, Array, JSON };
vm.createContext(ctx);
for (const s of scripts) vm.runInContext(s, ctx, { filename: 'tod2_armory.html' });
const tabs = Object.values(ids).filter(e => e.dataset.tab);
assert(tabs.length >= 5, 'tabs missing');
for (const t of tabs) assert(t.innerHTML.length > 200, `tab "${t.dataset.tab}" rendered empty`);
// click every DPS chip / filter chip so the redraw paths run too
for (const t of tabs) for (const c of t.children) if (c.listeners.click) c.listeners.click({ currentTarget: c, target: { closest: () => c } });
console.log(`TOD2 ARMORY OK - script runs, ${tabs.length} tabs render (${tabs.map(t => t.dataset.tab).join(', ')})`);
