// Run: PLAYWRIGHT_MODULE=/path/to/playwright/index.mjs node browser_check.mjs [artifact-dir]
// Browser-only development dependency; the deployed site is entirely dependency-free.
import assert from 'node:assert/strict';
import http from 'node:http';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import fs from 'node:fs/promises';
import { STORAGE_KEY, NOTE_LIMIT } from '../app.mjs';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const artifacts = path.resolve(process.argv[2] || path.join(root, 'test-results'));
const modulePath = process.env.PLAYWRIGHT_MODULE;
const { chromium } = await import(modulePath ? pathToFileURL(path.resolve(modulePath)).href : 'playwright');
await fs.mkdir(artifacts, { recursive: true });
const catalog = JSON.parse((await fs.readFile(path.join(root, 'catalog.json'), 'utf8')).replace(/^\uFEFF/, ''));
const config = JSON.parse((await fs.readFile(path.join(root, 'config.json'), 'utf8')).replace(/^\uFEFF/, ''));
const assets = new Set(['index.html', 'app.mjs', 'styles.css', 'config.json', 'catalog.json', 'favicon.svg']);
const contentTypes = { '.html': 'text/html; charset=utf-8', '.mjs': 'application/javascript; charset=utf-8', '.css': 'text/css; charset=utf-8', '.json': 'application/json; charset=utf-8', '.svg': 'image/svg+xml' };
const server = http.createServer(async (request, response) => {
  const url = new URL(request.url, 'http://127.0.0.1');
  const name = url.pathname === '/AxisMeld/' ? 'index.html' : url.pathname.replace(/^\/AxisMeld\//, '');
  if (!url.pathname.startsWith('/AxisMeld/') || !assets.has(name)) { response.writeHead(404); response.end(); return; }
  try {
    response.writeHead(200, { 'Content-Type': contentTypes[path.extname(name)], 'Cache-Control': 'no-store' });
    response.end(await fs.readFile(path.join(root, name)));
  } catch { response.writeHead(500); response.end(); }
});
await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
const origin = `http://127.0.0.1:${server.address().port}`;
const url = `${origin}/AxisMeld/`;
const browser = await chromium.launch({ headless: true, ...(process.env.BROWSER_EXECUTABLE ? { executablePath: process.env.BROWSER_EXECUTABLE } : { channel: 'msedge' }) });
const checks = [];
const consoleErrors = [];
const requests = [];
const record = (name, detail = {}) => { checks.push({ name, result: 'passed', ...detail }); console.log(`PASS ${name}`); };
const ready = page => page.waitForSelector('html[data-ready="true"]');
const assertGroupedCards = async (page, expectedItems) => {
  const expected = [];
  let previousGroup;
  for (const item of expectedItems) {
    if (item.group !== previousGroup) {
      expected.push({ kind: 'heading', group: item.group });
      previousGroup = item.group;
    }
    expected.push({ kind: 'card', id: item.id });
  }
  const actual = await page.locator('#test-list').evaluate(list => [...list.children].map(node => {
    if (node.matches('h2.test-group-heading')) return { kind: 'heading', group: node.textContent };
    if (node.matches('.test-card')) return { kind: 'card', id: node.dataset.testId };
    return { kind: 'unexpected', tag: node.tagName };
  }));
  assert.deepEqual(actual, expected, 'each visible group needs one heading immediately before its cards, including page continuations');
};
try {
  const context = await browser.newContext({ viewport: { width: 1365, height: 900 }, acceptDownloads: true });
  const page = await context.newPage();
  page.on('pageerror', error => consoleErrors.push(error.message));
  page.on('request', request => requests.push(request.url()));
  await page.goto(url);
  await ready(page);
  const active = catalog.items.filter(item => !item.superseded);
  assert.equal(await page.locator('#count-all').textContent(), String(active.length));
  assert.equal(await page.locator('#count-untested').textContent(), String(active.length));
  assert.equal(await page.locator('#count-tested').textContent(), '0');
  assert.equal(await page.locator('#count-passed').textContent(), '0');
  assert.equal(await page.locator('.test-card').count(), Math.min(50, active.length));
  assert.ok(await page.locator('.privacy-notice').textContent().then(t => t.includes('≠ 已提交维护者')));
  assert.equal(await page.evaluate(key => localStorage.getItem(key), STORAGE_KEY), null);
  await page.screenshot({ path: path.join(artifacts, 'desktop-initial.png') });
  record(`${catalog.items.length}-item catalog loads under /AxisMeld/; fresh visitor has zero tested`, { catalog: catalog.items.length, active: active.length, initialDOM: await page.locator('.test-card').count() });

  const pageCount = Math.ceil(active.length / 50);
  const paginatedIds = [];
  for (let number = 1; number <= pageCount; number += 1) {
    const visible = active.slice((number - 1) * 50, number * 50);
    await assertGroupedCards(page, visible);
    assert.equal(await page.locator('#page-label').textContent(), `${number} / ${pageCount} 页`);
    assert.equal(await page.locator('#previous-page').isDisabled(), number === 1);
    assert.equal(await page.locator('#next-page').isDisabled(), number === pageCount);
    paginatedIds.push(...await page.locator('.test-card').evaluateAll(cards => cards.map(card => card.dataset.testId)));
    if (number < pageCount) await page.locator('#next-page').click();
  }
  assert.deepEqual(paginatedIds, active.map(item => item.id), 'pagination must not omit, duplicate or reorder IDs');
  for (let number = pageCount; number > 1; number -= 1) await page.locator('#previous-page').click();
  await assertGroupedCards(page, active.slice(0, 50));
  record('pagination limits records to 50 and repeats the correct group headings on every page', { pages: pageCount, ids: paginatedIds.length });

  const groupedOptions = await page.locator('#group-filter optgroup').evaluateAll(groups => groups.map(group => ({
    label: group.label, values: [...group.children].map(option => option.value),
    labels: [...group.children].map(option => option.textContent),
  })));
  assert.deepEqual(groupedOptions.map(group => group.label), ['热盒', '菜单', '通用', '其他']);
  const catalogGroups = [...new Set(catalog.items.map(item => item.group))];
  assert.deepEqual(groupedOptions.flatMap(group => group.values), catalogGroups);
  for (const group of groupedOptions) {
    assert.ok(group.values.every(value => value.startsWith(`${group.label} · `)));
    assert.deepEqual(group.labels, group.values.map(value => value.slice(`${group.label} · `.length)));
  }
  const entryGroups = catalogGroups.filter(group => /^(热盒|菜单) · /.test(group));
  for (const family of ['热盒', '菜单']) assert.ok(active.some(item => item.group.startsWith(`${family} · `)));
  for (const group of entryGroups) {
    await page.locator('#group-filter').selectOption(group);
    const matching = active.filter(item => item.group === group);
    await assertGroupedCards(page, matching.slice(0, 50));
    assert.ok((await page.locator('#results-summary').textContent()).includes(`/ ${matching.length} 项`));
  }
  await page.screenshot({ path: path.join(artifacts, 'desktop-menu-category.png') });
  await page.locator('#clear-filters').click();
  record('hotbox and menu categories filter exact stable IDs within four optgroups', { entryGroups: entryGroups.length, groups: catalogGroups.length });

  await page.locator('#recent-toggle').click();
  assert.equal(await page.locator('.test-card').count(), catalog.items.filter(item => item.isNew && !item.superseded).length);
  const targetItem = catalog.items.find(item => item.isNew && !item.superseded) || active[0];
  const id = targetItem.id;
  const card = page.locator(`[data-test-id="${id}"]`);
  const testNote = '中文备注 & ? # + / β\n<img src=x onerror="window.injected=1">\n第二行：菜单未显示。';
  const testBuild = 'candidate-测试 & β';
  await card.locator('summary').click();
  await card.locator('textarea').fill(testNote);
  await card.locator('[data-record-build]').fill(testBuild);
  await card.locator('[data-record-build]').press('Tab');
  await card.locator('[data-record-status]').selectOption('failed');
  assert.equal(await page.locator('#count-failed').textContent(), '1');
  assert.equal(await page.locator('#count-tested').textContent(), '1');
  assert.equal(await page.evaluate(() => window.injected), undefined);
  await page.reload();
  await ready(page);
  await page.locator('#search-input').fill(id);
  assert.equal(await page.locator(`[data-record-status="${id}"]`).inputValue(), 'failed');
  await page.locator(`[data-test-id="${id}"] summary`).click();
  assert.equal(await page.locator(`[data-test-id="${id}"] textarea`).inputValue(), testNote);
  assert.equal(await page.locator(`[data-record-build="${id}"]`).inputValue(), testBuild);
  await page.locator('#default-build').fill('next-build');
  await page.locator('#default-build').press('Tab');
  assert.equal(await page.locator(`[data-record-build="${id}"]`).inputValue(), testBuild);
  record('state, Unicode note and per-item version survive reload; default change preserves prior version');

  await page.locator(`[data-feedback-id="${id}"]`).click();
  const href = await page.locator('#submit-feedback-link').getAttribute('href');
  const issue = new URL(href);
  assert.equal(issue.origin, 'https://github.com');
  assert.equal(issue.pathname, '/AngelHob/AxisMeld/issues/new');
  assert.equal(issue.searchParams.get('labels'), 'test-feedback');
  const draft = await page.locator('#feedback-body').inputValue();
  assert.equal(issue.searchParams.get('body'), draft);
  assert.ok(draft.includes(id) && draft.includes(testNote) && draft.includes(testBuild) && draft.includes('失败'));
  assert.equal(await page.locator('#submit-feedback-link').getAttribute('rel'), 'noopener noreferrer');
  await page.locator('#close-dialog').click();
  record('GitHub Issue URL round-trips exact ID, version, result and multiline special-character note; never submitted');

  const longNote = '中'.repeat(NOTE_LIMIT);
  await page.locator(`[data-test-id="${id}"] textarea`).fill(longNote);
  assert.equal(await page.locator(`[data-test-id="${id}"] textarea`).getAttribute('maxlength'), String(NOTE_LIMIT));
  await page.locator(`[data-feedback-id="${id}"]`).click();
  assert.equal(await page.locator('#long-feedback-warning').isVisible(), true);
  assert.ok((await page.locator('#feedback-body').inputValue()).includes(longNote));
  const shortIssue = new URL(await page.locator('#submit-feedback-link').getAttribute('href'));
  assert.equal(shortIssue.searchParams.has('body'), false);
  assert.ok(shortIssue.href.length < 1000);
  assert.ok((await page.locator('#submit-feedback-link').textContent()).includes('粘贴提交'));
  await page.locator('#close-dialog').click();
  await page.locator(`[data-test-id="${id}"] textarea`).fill(testNote);
  record('2000-character limit and long-URL warning preserve complete feedback');

  const [download] = await Promise.all([page.waitForEvent('download'), page.locator('#export-button').click()]);
  const downloadPath = path.join(artifacts, 'visitor-export.json');
  await download.saveAs(downloadPath);
  const exported = JSON.parse(await fs.readFile(downloadPath, 'utf8'));
  assert.equal(exported.submittedToMaintainer, false);
  assert.equal(exported.storageScope, 'this-browser-only');
  assert.equal(exported.records[id].note, testNote);
  assert.equal(exported.records[id].buildId, testBuild);
  record('JSON backup downloads real local records and explicitly says not submitted');

  await page.locator('#clear-filters').click();
  await page.locator('[data-filter="failed"]').click();
  assert.equal(await page.locator('.test-card').count(), 1);
  await page.locator('[data-filter="passed"]').click();
  assert.equal(await page.locator('.test-card').count(), 0);
  await page.locator('[data-filter="tested"]').click();
  assert.equal(await page.locator('.test-card').count(), 1);
  await page.locator('#clear-filters').click();
  const group = active[0].group;
  await page.locator('#group-filter').selectOption(group);
  const groupCount = active.filter(item => item.group === group).length;
  assert.equal(await page.locator('.test-card').count(), Math.min(50, groupCount));
  await page.locator('#clear-filters').click();
  const historical = catalog.items.find(item => item.superseded);
  if (historical) {
    await page.locator('#search-input').fill(historical.id);
    assert.equal(await page.locator(`[data-test-id="${historical.id}"] .history-badge`).isVisible(), true);
    await page.locator(`[data-test-id="${historical.id}"] summary`).click();
    assert.ok((await page.locator(`[data-test-id="${historical.id}"] .history-notice`).textContent()).includes('不作为当前构建'));
    await page.locator('#clear-filters').click();
    await page.locator('#history-toggle').check();
    assert.ok((await page.locator('#results-summary').textContent()).includes(`/ ${catalog.items.length} 项`));
  }
  record('status, group, recent and history filters; search finds historical IDs with non-acceptance notice');

  await page.locator('#clear-filters').click();
  await page.setViewportSize({ width: 390, height: 844 });
  assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= document.documentElement.clientWidth), 'narrow-screen horizontal overflow');
  await page.screenshot({ path: path.join(artifacts, 'mobile-initial.png') });
  await page.locator('#recent-toggle').click();
  if (!await page.locator(`[data-test-id="${id}"] details`).evaluate(details => details.open)) {
    await page.locator(`[data-test-id="${id}"] summary`).click();
  }
  assert.equal(await page.locator(`[data-test-id="${id}"] details`).evaluate(details => details.open), true);
  await page.locator(`[data-test-id="${id}"]`).scrollIntoViewIfNeeded();
  assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= document.documentElement.clientWidth));
  await page.screenshot({ path: path.join(artifacts, 'mobile-expanded.png') });
  await page.setViewportSize({ width: 1365, height: 900 });
  await page.locator('#page-title').scrollIntoViewIfNeeded();
  await page.screenshot({ path: path.join(artifacts, 'desktop-recent.png') });
  record('390px viewport has no horizontal overflow, including expanded notes and steps');

  const freshContext = await browser.newContext();
  const freshPage = await freshContext.newPage();
  await freshPage.goto(url);
  await ready(freshPage);
  assert.equal(await freshPage.locator('#count-tested').textContent(), '0');
  await freshContext.close();
  record('separate visitor context never inherits another visitor record');

  // Seed an old browser ledger in an isolated context, then change only the catalog.
  const legacyKey = 'axismeld-public-test-ledger:v1';
  assert.equal(STORAGE_KEY, legacyKey, 'regrouping must keep the existing browser storage key');
  const legacyRecords = {
    'GU-28': { status: 'failed', note: '重新分类前保存的热盒备注 & 第一行\n第二行', buildId: '18px-hotbox-before-regrouping', updatedAt: '2026-10-11T15:50:00.000Z' },
    'MB-40': { status: 'passed', note: '菜单记录独立保留 β', buildId: '18px-menu-before-regrouping', updatedAt: '2026-10-11T15:51:00.000Z' },
  };
  const legacyState = { schemaVersion: 1, defaultBuildId: 'saved-before-regrouping', records: legacyRecords };
  const legacyJSON = JSON.stringify(legacyState);
  const oldCatalog = { ...catalog, items: [...catalog.items].reverse().map(item => ({ ...item, group: `旧开发批次：${item.id.split('-')[0]}` })) };
  assert.notDeepEqual(oldCatalog.items.map(item => item.id), catalog.items.map(item => item.id));
  for (const id of Object.keys(legacyRecords)) assert.ok(active.some(item => item.id === id), `missing active migration fixture ${id}`);
  const legacyContext = await browser.newContext({ acceptDownloads: true, storageState: {
    cookies: [], origins: [{ origin, localStorage: [{ name: legacyKey, value: legacyJSON }] }],
  } });
  const legacyPage = await legacyContext.newPage();
  legacyPage.on('pageerror', error => consoleErrors.push(error.message));
  const oldCatalogRoute = route => route.fulfill({ json: oldCatalog });
  await legacyPage.route('**/catalog.json', oldCatalogRoute);
  const assertLegacyRecords = async items => {
    assert.equal(await legacyPage.locator('#count-tested').textContent(), '2');
    assert.equal(await legacyPage.locator('#count-passed').textContent(), '1');
    assert.equal(await legacyPage.locator('#count-failed').textContent(), '1');
    assert.equal(await legacyPage.locator('#default-build').inputValue(), legacyState.defaultBuildId);
    for (const [id, saved] of Object.entries(legacyRecords)) {
      await legacyPage.locator('#search-input').fill(id);
      const matching = items.find(item => item.id === id);
      await assertGroupedCards(legacyPage, [matching]);
      const savedCard = legacyPage.locator(`[data-test-id="${id}"]`);
      assert.equal(await savedCard.locator('[data-record-status]').inputValue(), saved.status);
      await savedCard.locator('summary').click();
      assert.equal(await savedCard.locator('textarea').inputValue(), saved.note);
      assert.equal(await savedCard.locator('[data-record-build]').inputValue(), saved.buildId);
    }
    assert.equal(await legacyPage.evaluate(key => localStorage.getItem(key), legacyKey), legacyJSON, 'loading and filtering must not rewrite old records');
  };
  await legacyPage.goto(url);
  await ready(legacyPage);
  await assertLegacyRecords(oldCatalog.items);
  await legacyPage.unroute('**/catalog.json', oldCatalogRoute);
  await legacyPage.reload();
  await ready(legacyPage);
  await assertLegacyRecords(catalog.items);
  const [legacyDownload] = await Promise.all([legacyPage.waitForEvent('download'), legacyPage.locator('#export-button').click()]);
  const legacyExportPath = path.join(artifacts, 'legacy-records-after-regrouping.json');
  await legacyDownload.saveAs(legacyExportPath);
  const legacyExport = JSON.parse(await fs.readFile(legacyExportPath, 'utf8'));
  assert.deepEqual(legacyExport.records, legacyRecords);
  assert.equal(legacyExport.defaultBuildId, legacyState.defaultBuildId);
  assert.equal(legacyExport.submittedToMaintainer, false);
  await legacyContext.close();
  record('GU-28 and MB-40 retain old status, notes, versions and timestamps after catalog regrouping and reordering');

  const maliciousContext = await browser.newContext();
  const malicious = await maliciousContext.newPage();
  malicious.on('pageerror', error => consoleErrors.push(error.message));
  const attack = '<img src=x onerror="window.injected=1"><script>window.injected=2</script>';
  await malicious.route('**/catalog.json', route => route.fulfill({ json: { items: [{ id: 'XSS-1', title: attack, group: attack, steps: [attack], expected: [attack], maintainerStatus: 'passed' }] } }));
  await malicious.route('**/config.json', route => route.fulfill({ json: { ...config, releaseUrl: 'https://private.chatgpt.site/', feedback: { mode: 'external', externalUrl: 'https://127.0.0.1/private', listUrl: 'file:///C:/private' } } }));
  await malicious.goto(url);
  await ready(malicious);
  assert.equal(await malicious.locator('.test-title').textContent(), attack);
  assert.equal(await malicious.locator('.test-card img, .test-card script').count(), 0);
  assert.equal(await malicious.evaluate(() => window.injected), undefined);
  assert.equal(await malicious.locator('#download-link').isVisible(), false);
  assert.equal(await malicious.locator('#feedback-list-link').isVisible(), false);
  assert.equal(await malicious.locator('#count-tested').textContent(), '0');
  await malicious.locator('summary').click();
  await malicious.locator('[data-feedback-id]').click();
  assert.equal(await malicious.locator('#submit-feedback-link').isVisible(), false);
  await malicious.locator('#close-dialog').click();
  await malicious.locator('#search-input').fill(attack);
  assert.equal(await malicious.locator('.test-card').count(), 1);
  await maliciousContext.close();
  record('injected catalog/search text is inert; local/private/unsafe outbound configuration is rejected');

  const blockedContext = await browser.newContext();
  const blocked = await blockedContext.newPage();
  await blocked.addInitScript(() => { Storage.prototype.setItem = function () { throw new DOMException('Unavailable', 'QuotaExceededError'); }; });
  await blocked.goto(url);
  await ready(blocked);
  await blocked.locator('[data-record-status]').first().selectOption('passed');
  assert.equal(await blocked.locator('#storage-warning').isVisible(), true);
  assert.ok((await blocked.locator('#save-status').textContent()).includes('未能持久保存'));
  await blockedContext.close();
  record('blocked storage gives visible warning and never claims successful persistence');

  assert.deepEqual(consoleErrors, []);
  assert.ok(requests.every(request => request.startsWith(origin)), `Unexpected outbound request: ${requests.filter(request => !request.startsWith(origin))}`);
  record('no browser script errors or external background requests');
  await context.close();
} finally {
  await browser.close();
  await new Promise(resolve => server.close(resolve));
  await fs.writeFile(path.join(artifacts, 'browser-report.json'), JSON.stringify({ checks, consoleErrors, requests }, null, 2));
}
console.log(`${checks.length} browser checks passed; artifacts: ${artifacts}`);
