const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const html = fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8');
const initScript = html.match(/<script id="theme-init">([\s\S]*?)<\/script>/)[1];
const controlsScript = html.match(/<script id="theme-controls">([\s\S]*?)<\/script>/)[1];
function openPage({saved = null, dark = false, blocked = false} = {}) {
  const root = {dataset: {}};
  const attrs = {};
  const events = {};
  const media = {matches: dark, addEventListener: (_, handler) => { events.system = handler; }};
  let ready = false;
  const button = {hidden: true, setAttribute: (key, value) => { attrs[key] = value; },
    addEventListener: (_, handler) => { events.click = handler; }};
  const store = {value: saved};
  const window = {matchMedia: () => media, addEventListener: (key, handler) => { events[key] = handler; }};
  const context = vm.createContext({window,
    document: {documentElement: root, getElementById: () => ready ? button : null},
    localStorage: {
      getItem: () => { if (blocked) throw Error('blocked'); return store.value; },
      setItem: (_, value) => { if (blocked) throw Error('blocked'); store.value = value; },
    },
  });
  vm.runInContext(initScript, context);
  const initialTheme = root.dataset.theme;
  ready = true;
  vm.runInContext(controlsScript, context);
  return {root, attrs, events, media, button, store, initialTheme};
}
let page = openPage({dark: true});
assert.equal(page.initialTheme, 'dark');
assert.equal(page.attrs['aria-pressed'], 'true');
assert.equal(page.button.hidden, false);
page.events.click();
assert.equal(page.root.dataset.theme, 'light');
assert.equal(page.attrs['aria-pressed'], 'false');
assert.equal(page.store.value, 'light');
assert.equal(openPage({dark: true, saved: page.store.value}).initialTheme, 'light');
page.media.matches = true;
page.events.system();
assert.equal(page.root.dataset.theme, 'light');
page = openPage();
page.media.matches = true;
page.events.system();
assert.equal(page.root.dataset.theme, 'dark');
page.events.storage({key: 'classBoardTheme', newValue: 'light'});
assert.equal(page.root.dataset.theme, 'light');
page.events.storage({key: 'unrelated', newValue: 'dark'});
assert.equal(page.root.dataset.theme, 'light');
page.events.storage({key: null, newValue: null});
assert.equal(page.root.dataset.theme, 'dark');
page = openPage({saved: 'invalid', dark: true});
assert.equal(page.initialTheme, 'dark');
page = openPage({blocked: true});
page.events.click();
assert.equal(page.root.dataset.theme, 'dark');
assert.equal(page.attrs['aria-pressed'], 'true');
assert.ok(html.indexOf('id="theme-init"') < html.indexOf('<style>'));
assert.match(html, /<header class="title-row">[\s\S]*?<h1>.*?<\/h1>[\s\S]*?id="themeToggle"[\s\S]*?<\/header>/);
console.log('主題測試通過：初始模式、切換、儲存偏好、系統變更、跨分頁、儲存受限及按鈕狀態');
