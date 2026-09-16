const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const test = require('node:test');
const assert = require('node:assert/strict');
const source = fs.readFileSync(path.join(__dirname, '../src/pedit/static/app.js'), 'utf8');
const saveCode = source.slice(source.indexOf('function progressPayload()'), source.indexOf('async function saveProgress()'));
const restoreCode = source.slice(source.indexOf('async function resumeSavedProgress()'), source.indexOf('\n// Restore only after an explicit user action'));

function context(progress) {
  const element = {classList: {add() {}, remove() {}}};
  const ctx = {
    state: {}, Map, Set, JSON, Math, Number, Object, String, encodeURIComponent,
    localStorage: {getItem(key) { return key === 'pedit.oss.v1.lastProgress' ? '{"id":"test-session"}' : null; }},
    fetch: async () => ({ok: true, json: async () => ({id: 'test-session', name: 'test.pdf', pageCount: 1, progress})}),
    els: new Proxy({}, {get: () => element}),
    console: {warn: (...args) => {throw new Error(args.join(' '));}},
    ensurePageNumberTakeoverSet: () => ctx.state.pageNumberManualTakeovers,
  };
  for (const name of ['addPageNumberSlot', 'renderPageNumberTemplateSlots', 'updateChangeCount',
    'updateHistoryButtons', 'clearProps', 'buildThumbnails', 'updateEngineUi', 'loadPage', 'toast']) ctx[name] = () => {};
  vm.createContext(ctx);
  vm.runInContext(saveCode + '\n' + restoreCode, ctx);
  return ctx;
}

test('actual browser progress functions retain glyph bytes, anchors, edits and libraries', async () => {
  const asset = {rgbaDataUrl: 'data:image/png;base64,c3ludGhldGlj', sourceScale: 4,
    sourceGlyphLeftOffsetPx: 2, sourceGlyphTopOffsetPx: 3, mode: 'original'};
  const progress = {schemaVersion: 1, currentPage: 0, edits: [['e', {newText: '456'}]],
    glyphLibrary: [['4', {documentId: 'test-session', asset}]], blockLibrary: [['456', {asset}]],
    pageNumberTemplates: {A: null, B: null}, pageNumberPageOverrides: {},
    pageNumberManualTakeovers: ['0:A'], versionHistory: [], previewQuality: 'high', changeLogTombstones: []};
  const ctx = context(progress);
  await ctx.resumeSavedProgress();
  assert.equal(ctx.state.glyphLibrary.get('4').asset.rgbaDataUrl, asset.rgbaDataUrl);
  assert.equal(ctx.state.blockLibrary.get('456').asset.sourceGlyphTopOffsetPx, 3);
  assert.equal(ctx.state.edits.get('e').newText, '456');
  const serialized = JSON.parse(JSON.stringify(ctx.progressPayload()));
  assert.deepEqual(serialized.glyphLibrary, progress.glyphLibrary);
  assert.deepEqual(serialized.blockLibrary, progress.blockLibrary);
  assert.deepEqual(serialized.pageNumberManualTakeovers, ['0:A']);
  assert.equal(serialized.schemaVersion, 1);
});

test('older progress without asset libraries remains loadable', async () => {
  const ctx = context({edits: [], currentPage: 0});
  await ctx.resumeSavedProgress();
  assert.equal(ctx.state.glyphLibrary.size, 0);
  assert.equal(ctx.state.blockLibrary.size, 0);
});

test('complete UI script starts empty even with saved progress in browser storage', () => {
  const nodes = new Map();
  const node = () => ({value: '', textContent: '', innerHTML: '', disabled: false,
    style: {setProperty() {}}, dataset: {}, children: [],
    classList: {add() {}, remove() {}, toggle() {}, contains() {return false;}},
    addEventListener() {}, querySelectorAll() {return [];},
    querySelector() {return node();}, appendChild() {}, setAttribute() {},
    getAttribute() {return '';}, getBoundingClientRect() {return {width: 800, height: 600};}});
  const document = {querySelector(selector) {
    if (!nodes.has(selector)) nodes.set(selector, node());
    return nodes.get(selector);
  }, querySelectorAll() {return [];}, createElement: node, body: node(),
  addEventListener() {}};
  let storageReads = 0, requests = 0;
  const ctx = {document, window: {addEventListener() {}, devicePixelRatio: 1},
    localStorage: {getItem() {storageReads++; return '{"id":"saved-session","name":"test.pdf"}';}},
    fetch: () => {requests++; throw new Error('Unexpected startup request');},
    setTimeout() {}, clearTimeout() {}, requestAnimationFrame() {}, console,
    ResizeObserver: class {observe() {}},
    Map, Set, JSON, Object, Number, String, Math, Date, URL};
  vm.createContext(ctx);
  vm.runInContext(source, ctx);
  const initial = vm.runInContext('state', ctx);
  assert.equal(initial.id, null);
  assert.equal(initial.name, null);
  assert.equal(initial.pageCount, 0);
  assert.equal(initial.edits.size, 0);
  assert.equal(initial.glyphLibrary.size, 0);
  assert.equal(initial.blockLibrary.size, 0);
  assert.equal(initial.versionHistory.length, 0);
  assert.equal(storageReads, 0);
  assert.equal(requests, 0);
  assert.equal(typeof nodes.get('#resumeProgressBtn').onclick, 'function');
});
