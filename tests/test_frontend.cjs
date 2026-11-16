// 在最小 DOM 測試替身中驗證渲染邏輯；不取代實際瀏覽器排版檢查。
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const rootPath = path.join(__dirname, '..');
const html = fs.readFileSync(path.join(rootPath, 'index.html'), 'utf8');
const script = html.match(/<script>([\s\S]*?)<\/script>/)[1];
class Element {
  constructor(tag) { this.tag = tag; this.childNodes = []; this.style = {}; this.text = ''; }
  replaceChildren(...nodes) { this.childNodes = nodes; this.text = ''; }
  appendChild(node) { this.childNodes.push(node); return node; }
  append(...nodes) { this.childNodes.push(...nodes); }
  set textContent(value) { this.text = value; this.childNodes = []; }
  get textContent() { return this.text + this.childNodes.map(node => node.textContent).join(''); }
  set innerHTML(value) { this.html = value; this.childNodes = []; }
  get innerHTML() { return this.html ?? this.text.replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;'); }
}
async function render(config, ok = true) {
  const nodes = Object.fromEntries(['examList','homeworkList','matterList','noticeBar','quickLinks','calendarWrap'].map(id => [id,new Element('div')]));
  const context = vm.createContext({
    document: {getElementById: id => nodes[id], createElement: tag => new Element(tag),
      createTextNode: text => ({textContent: text})},
    Date, URL, console,
    fetch: async () => ({ok, status: 404, json: async () => config}),
  });
  vm.runInContext(script, context);
  await new Promise(resolve => setImmediate(resolve));
  return nodes;
}
(async () => {
  const headings = [...html.matchAll(/<h2>(.*?)<\/h2>/g)].map(match => match[1]);
  assert.deepEqual(headings, ['近期小考','近期作業','近期事項','常用連結','行事曆']);
  assert.equal((html.match(/fetch\(/g) || []).length, 1);
  const config = JSON.parse(fs.readFileSync(path.join(rootPath, 'config.json'), 'utf8'));
  config.homework = [{date:'2099-12-01',item:'國文作文',link:'https://example.com/homework'},
    {date:'2000-01-01',item:'舊作業',link:''}];
  config.exams[0].subject = '<img src=x onerror=alert(1)>';
  let nodes = await render(config);
  assert.equal(nodes.examList.childNodes.length, 9);
  assert.ok(nodes.examList.childNodes[0].innerHTML.includes('&lt;img'));
  assert.equal(nodes.homeworkList.childNodes.length, 1);
  assert.equal(nodes.homeworkList.childNodes[0].childNodes[1].textContent, '國文作文');
  assert.equal(nodes.homeworkList.childNodes[0].childNodes[2].childNodes[0].href, 'https://example.com/homework');
  assert.equal(nodes.quickLinks.childNodes.length, 4);
  assert.equal(nodes.calendarWrap.childNodes[0].src, config.calendar.url);
  config.homework[0].link = 'javascript:alert(1)';
  nodes = await render(config);
  assert.equal(nodes.homeworkList.childNodes[0].childNodes[2].childNodes.length, 0);
  const empty = {exams:[],homework:[],matters:[],links:[],calendar:{url:''},cleanupPolicy:'never'};
  nodes = await render(empty);
  assert.equal(nodes.calendarWrap.textContent, '尚未設定行事曆');
  assert.equal(nodes.quickLinks.textContent, '目前沒有常用連結');
  assert.equal(nodes.homeworkList.childNodes[0].textContent, '目前沒有近期作業');
  nodes = await render(null, false);
  for (const id of ['examList','homeworkList','matterList','quickLinks','calendarWrap']) {
    assert.ok(nodes[id].textContent.includes('HTTP 404'));
  }
  console.log('前端邏輯驗證通過：區塊順序、資料、作業連結、跳脫、空狀態及錯誤狀態');
})().catch(error => { console.error(error); process.exitCode = 1; });
