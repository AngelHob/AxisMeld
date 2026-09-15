import assert from 'node:assert/strict';
import { feedbackDraft, filterItems, normalizeCatalog, normalizeState, publicUrl, recordFor, NOTE_LIMIT } from '../app.mjs';

const config = { repoUrl: 'https://github.com/AngelHob/AxisMeld', feedback: { mode: 'github', label: 'test-feedback' } };
const items = normalizeCatalog({ items: [
  { id: 'MB-40', title: '菜单 & <svg onload=alert(1)>', group: '菜单', steps: ['打开菜单'], expected: ['图标完整'], maintainerStatus: 'tested', isNew: true },
  { id: 'MB-28', title: '历史入口', group: '菜单', steps: ['旧步骤'], expected: ['旧预期'], superseded: true, maintainerStatus: 'passed' },
] });
const state = normalizeState(null, 'build-1');
assert.equal(recordFor(state, 'MB-40').status, 'untested');
assert.equal(recordFor(state, 'MB-28').status, 'untested');
const filters = { query: '', status: 'all', group: '', recent: false, history: false };
assert.deepEqual(filterItems(items, state, filters).map(i => i.id), ['MB-40']);
assert.deepEqual(filterItems(items, state, { ...filters, query: 'MB-28' }).map(i => i.id), ['MB-28']);
state.records['MB-40'] = { status: 'failed', note: '中文 & ? # +\n<img src=x onerror=alert(1)>', buildId: '自测版本&β', updatedAt: '' };
assert.equal(filterItems(items, state, { ...filters, status: 'tested' }).length, 1);
assert.equal(filterItems(items, state, { ...filters, status: 'passed' }).length, 0);
const draft = feedbackDraft(config, items[0], state.records['MB-40']);
const url = new URL(draft.url);
assert.equal(url.pathname, '/AngelHob/AxisMeld/issues/new');
assert.equal(url.searchParams.get('body'), draft.body);
assert.equal(url.searchParams.get('title'), draft.title);
assert.equal(url.searchParams.get('labels'), 'test-feedback');
assert.ok(draft.body.includes(state.records['MB-40'].note));
assert.ok(draft.body.includes('自测版本&β'));
const long = feedbackDraft(config, items[0], { ...state.records['MB-40'], note: '中文'.repeat(NOTE_LIMIT / 2) });
assert.equal(long.long, true);
assert.ok(long.body.includes('中文'.repeat(NOTE_LIMIT / 2)));
assert.equal(new URL(long.url).searchParams.has('body'), false);
assert.ok(long.url.length < 1000);
for (const value of ['javascript:alert(1)', 'file:///D:/private', 'https://localhost/', 'https://127.0.0.1/', 'https://192.168.1.1/', 'https://172.18.0.1/', 'https://100.64.0.1/', 'https://[::1]/', 'https://private.chatgpt.site/', 'https://user:pass@github.com/', 'https://github.com.evil.test/', 'https://github.com:444/']) assert.equal(publicUrl(value, true), null, value);
for (const value of ['https://localhost/', 'https://127.0.0.1/', 'https://192.168.1.1/', 'https://172.18.0.1/', 'https://100.64.0.1/', 'https://[::1]/', 'https://private.chatgpt.site/', 'https://user:pass@example.com/']) assert.equal(publicUrl(value), null, value);
assert.equal(publicUrl('https://github.com/AngelHob/AxisMeld', true).host, 'github.com');
assert.equal(publicUrl('https://forms.example.com/public-feedback').host, 'forms.example.com');
assert.throws(() => normalizeCatalog({ items: [items[0], items[0]] }), /重复/);
const malformed = normalizeState({ records: { constructor: { status: 'failed' }, 'MB-40': { status: 'bogus', note: 123, buildId: null } } }, 'build-1');
assert.equal(recordFor(malformed, 'MB-40').status, 'untested');
assert.equal(recordFor(malformed, 'MB-40').note, '');
assert.equal(recordFor(malformed, 'MB-40').buildId, 'build-1');
console.log('PASS: visitor state isolation, filters, history, complete encoded feedback, long-note warning, unsafe URL rejection, data validation');
