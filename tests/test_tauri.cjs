const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const rootPath = path.resolve(__dirname, '..', process.argv[2] || '.');
const resourceBase = JSON.parse(fs.readFileSync(path.join(rootPath, 'project.json'), 'utf8')).syncUrl;
const html = fs.readFileSync(path.join(rootPath, 'src-tauri/index.html'), 'utf8');
const script = html.match(/<script>([\s\S]*?)<\/script>/)[1];

class Element {
  constructor() { this.childNodes = []; this.style = {}; this.events = {}; this.text = ''; }
  replaceChildren(...nodes) { this.childNodes = nodes; this.text = ''; }
  appendChild(node) { this.childNodes.push(node); return node; }
  append(...nodes) { this.childNodes.push(...nodes); }
  addEventListener(name, handler) { this.events[name] = handler; }
  set textContent(value) { this.text = value; this.childNodes = []; }
  get textContent() { return this.text + this.childNodes.map(node => node.textContent).join(''); }
  set innerHTML(value) { this.html = value; this.childNodes = []; }
  get innerHTML() { return this.html ?? this.text.replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;'); }
}
const fixture = () => ({
  exams: [{date:'2099-12-01', subject:'<img src=x onerror=alert(1)>', range:'第一課'}],
  homework: [{date:'2099-12-01', item:'作文', link:'https://example.com/work'}],
  matters: [{date:'2099-12-02', item:'班會', link:''}],
  links: [
    {label:'相對圖片', url:'https://example.com', image:'qr/test.png', hint:''},
    {label:'遠端圖片', url:'https://example.com', image:'https://example.com/test.png', hint:''},
    {label:'不安全連結', url:'javascript:alert(1)', image:'', hint:''},
  ],
  calendar: {url:'https://calendar.google.com/calendar/embed'},
});
const flush = () => new Promise(resolve => setImmediate(resolve));

function openPage() {
  const ids = ['examList','homeworkList','matterList','noticeBar','quickLinks','calendarWrap','syncStatus','refreshButton'];
  const nodes = Object.fromEntries(ids.map(id => [id, new Element()]));
  const documentEvents = {}, windowEvents = {}, timers = new Map(), requests = [], opened = [];
  let nextTimer = 0;
  let respond = async () => ({ok:true, json:async () => fixture()});
  const document = {
    visibilityState:'visible', getElementById:id => nodes[id],
    createElement:() => new Element(), createTextNode:text => ({textContent:text}),
    addEventListener:(name, handler) => { documentEvents[name] = handler; },
  };
  const context = vm.createContext({
    document, Date, URL, AbortController, console,
    window: {location:{href:'http://tauri.localhost/'},
      __TAURI__:{opener:{openUrl:async url => { opened.push(url); }}},
      addEventListener:(name, handler) => { windowEvents[name] = handler; },
      alert:() => assert.fail('unexpected alert'),
    },
    setTimeout:(callback, delay) => { const id = ++nextTimer; timers.set(id, {callback, delay}); return id; },
    clearTimeout:id => timers.delete(id),
    fetch:(url, options) => { requests.push({url, options}); return respond(url, options); },
  });
  vm.runInContext(script, context);
  return {nodes, context, document, documentEvents, windowEvents, timers, requests, opened,
    setResponse:handler => { respond = handler; }};
}

(async () => {
  const config = JSON.parse(fs.readFileSync(path.join(rootPath, 'src-tauri/tauri.conf.json')));
  assert.deepEqual(config.build.frontendDist, ['index.html']);
  const capability = JSON.parse(fs.readFileSync(path.join(rootPath, 'src-tauri/capabilities/default.json')));
  assert.ok(capability.permissions.some(permission => permission.identifier === 'opener:allow-open-url'));
  for (const match of html.matchAll(/<script[^>]*>([\s\S]*?)<\/script>/g)) new vm.Script(match[1]);
  const page = openPage();
  assert.equal(page.nodes.refreshButton.disabled, true);
  assert.equal([...page.timers.values()][0].delay, 15000);
  await flush();
  assert.equal(page.nodes.refreshButton.disabled, false);
  assert.equal(page.timers.size, 0);
  const request = page.requests[0];
  const requestUrl = new URL(request.url);
  assert.match(requestUrl.searchParams.get('v'), /^\d+$/);
  requestUrl.search = '';
  assert.equal(requestUrl.href, new URL('config.json', resourceBase).href);
  assert.equal(request.options.cache, 'no-store');
  assert.equal(request.options.credentials, 'omit');
  assert.equal(page.nodes.examList.childNodes.length, 1);
  assert.match(page.nodes.examList.childNodes[0].innerHTML, /&lt;img/);
  assert.equal(page.nodes.homeworkList.childNodes[0].childNodes[1].textContent, '作文');
  assert.equal(page.nodes.quickLinks.childNodes.length, 2);
  const imageUrl = new URL(page.nodes.quickLinks.childNodes[0].childNodes[0].src);
  assert.match(imageUrl.searchParams.get('v'), /^\d+$/);
  imageUrl.search = '';
  assert.equal(imageUrl.href, new URL('qr/test.png', resourceBase).href);
  const absoluteImage = new URL(page.nodes.quickLinks.childNodes[1].childNodes[0].src);
  if (absoluteImage.origin === new URL(resourceBase).origin) {
    assert.match(absoluteImage.searchParams.get('v'), /^\d+$/);
    absoluteImage.search = '';
  }
  assert.equal(absoluteImage.href, 'https://example.com/test.png');
  assert.equal(page.nodes.calendarWrap.childNodes[0].src, fixture().calendar.url);
  assert.match(page.nodes.syncStatus.textContent, /本次取得時間/);

  let prevented = false;
  page.documentEvents.click({target:{closest:() => ({href:'https://example.com/open'})},
    preventDefault:() => { prevented = true; }});
  await flush();
  assert.equal(prevented, true);
  assert.deepEqual(page.opened, ['https://example.com/open']);

  page.setResponse(async () => ({ok:false, status:503}));
  await vm.runInContext('loadConfig()', page.context);
  for (const id of ['examList','homeworkList','matterList','quickLinks','calendarWrap']) {
    assert.match(page.nodes[id].textContent, /無法取得遠端資料/);
  }
  assert.equal(page.nodes.noticeBar.style.display, 'none');
  assert.match(page.nodes.syncStatus.textContent, /HTTP 503/);
  assert.equal(page.nodes.refreshButton.disabled, false);

  page.setResponse((_, options) => new Promise((resolve, reject) => {
    options.signal.addEventListener('abort', () => reject(Object.assign(new Error(), {name:'AbortError'})));
  }));
  const pending = vm.runInContext('loadConfig()', page.context);
  const count = page.requests.length;
  await vm.runInContext('loadConfig()', page.context);
  assert.equal(page.requests.length, count);
  [...page.timers.values()][0].callback();
  await pending;
  assert.match(page.nodes.syncStatus.textContent, /連線逾時（15 秒）/);
  assert.equal(page.nodes.refreshButton.disabled, false);
  assert.equal(page.timers.size, 0);

  page.setResponse(async () => ({ok:true, json:async () => fixture()}));
  page.document.visibilityState = 'hidden';
  page.windowEvents.online();
  page.documentEvents.visibilitychange();
  assert.equal(page.requests.length, count);
  page.document.visibilityState = 'visible';
  page.documentEvents.visibilitychange();
  await flush();
  page.windowEvents.online();
  await flush();
  page.nodes.refreshButton.events.click();
  await flush();
  assert.equal(page.requests.length, count + 3);
  assert.match(page.nodes.syncStatus.textContent, /本次取得時間/);
  page.setResponse(async () => ({ok:true, json:async () => ({exams:[{}]})}));
  await vm.runInContext('loadConfig()', page.context);
  assert.match(page.nodes.syncStatus.textContent, /更新失敗/);
  assert.equal(page.nodes.refreshButton.disabled, false);
  console.log('App 測試通過：資產範圍、遠端渲染、QR、Opener、錯誤清除、逾時、重複抑制及更新事件');
})().catch(error => { console.error(error); process.exitCode = 1; });
