// Public catalog and local visitor records deliberately have separate lifecycles.
export const STORAGE_KEY = 'axismeld-public-test-ledger:v1';
export const PAGE_SIZE = 50;
export const NOTE_LIMIT = 2000;
const STATUS = Object.freeze({ untested: '待测试', tested: '已测试 · 未判定', passed: '通过', failed: '失败' });
const HISTORY_STATUS = Object.freeze({ pending: '待测试', untested: '待测试', tested: '已测试，未判定通过', passed: '通过', failed: '失败' });
const own = (object, key) => Object.prototype.hasOwnProperty.call(object, key);
const asText = (value, fallback = '') => typeof value === 'string' ? value : fallback;
const textArray = value => Array.isArray(value) ? value.filter(v => typeof v === 'string') : typeof value === 'string' && value ? [value] : [];

export function publicUrl(value, githubOnly = false) {
  if (!value || typeof value !== 'string') return null;
  try {
    const url = new URL(value);
    const host = url.hostname.toLowerCase();
    if (url.protocol !== 'https:' || url.username || url.password || url.port) return null;
    if (githubOnly) return host === 'github.com' ? url : null;
    if (!host.includes('.') || host.includes(':') || host.endsWith('.local') || host.endsWith('.localhost') || host.endsWith('.internal') || host === 'chatgpt.site' || host.endsWith('.chatgpt.site')) return null;
    if (/^\d+\.\d+\.\d+\.\d+$/.test(host)) {
      const [a, b] = host.split('.').map(Number);
      if (a === 0 || a === 10 || a === 127 || a >= 224 || (a === 169 && b === 254) || (a === 172 && b >= 16 && b <= 31) || (a === 192 && b === 168) || (a === 100 && b >= 64 && b <= 127)) return null;
    }
    return url;
  } catch { return null; }
}

export function normalizeCatalog(data) {
  const rawItems = Array.isArray(data) ? data : data?.items;
  if (!Array.isArray(rawItems)) throw new Error('测试清单格式不正确：缺少 items。');
  const seen = new Set();
  return rawItems.map((raw, index) => {
    if (!raw || typeof raw !== 'object' || !/^[A-Za-z0-9_.:-]{1,80}$/.test(raw.id || '')) throw new Error(`第 ${index + 1} 项缺少有效测试编号。`);
    if (seen.has(raw.id)) throw new Error(`测试编号重复：${raw.id}`);
    seen.add(raw.id);
    if (!asText(raw.title)) throw new Error(`测试 ${raw.id} 缺少标题。`);
    return {
      id: raw.id, title: raw.title, group: asText(raw.group, '其他'),
      steps: textArray(raw.steps), expected: textArray(raw.expected),
      isNew: raw.isNew === true, superseded: raw.superseded === true,
      maintainerStatus: own(HISTORY_STATUS, raw.maintainerStatus) ? raw.maintainerStatus : null,
    };
  });
}

export function normalizeState(raw, buildId) {
  const state = { schemaVersion: 1, defaultBuildId: asText(raw?.defaultBuildId, buildId).slice(0, 120), records: Object.create(null) };
  if (raw && typeof raw.records === 'object' && raw.records !== null && !Array.isArray(raw.records)) {
    for (const [id, record] of Object.entries(raw.records)) {
      if (!/^[A-Za-z0-9_.:-]{1,80}$/.test(id) || !record || typeof record !== 'object') continue;
      state.records[id] = {
        status: own(STATUS, record.status) ? record.status : 'untested',
        note: asText(record.note).slice(0, NOTE_LIMIT),
        buildId: asText(record.buildId, buildId).slice(0, 120),
        updatedAt: asText(record.updatedAt),
      };
    }
  }
  return state;
}

export function recordFor(state, id) {
  return own(state.records, id) ? state.records[id] : { status: 'untested', note: '', buildId: state.defaultBuildId, updatedAt: '' };
}

export function filterItems(items, state, filters) {
  const query = filters.query.trim().toLocaleLowerCase();
  return items.filter(item => {
    // An explicit search also finds old IDs without making them current acceptance criteria.
    if (item.superseded && !filters.history && !query) return false;
    if (filters.group && item.group !== filters.group) return false;
    if (filters.recent && !item.isNew) return false;
    const status = recordFor(state, item.id).status;
    if (filters.status === 'tested' && status === 'untested') return false;
    if (!['all', 'tested'].includes(filters.status) && status !== filters.status) return false;
    return !query || [item.id, item.title, item.group, ...item.steps, ...item.expected, recordFor(state, item.id).note].join('\n').toLocaleLowerCase().includes(query);
  });
}

export function feedbackDraft(config, item, record) {
  const result = STATUS[record.status] || STATUS.untested;
  const body = [
    '## 测试信息', `- 测试编号：${item.id}`, `- 测试项目：${item.title}`,
    `- 测试版本：${record.buildId || '未填写'}`, `- 测试结果：${result}`,
    ...(item.superseded ? ['- 条目性质：历史记录，不作为当前构建验收'] : []),
    '', '## 实际结果与备注', record.note || '（请补充实际结果、复现步骤或截图）',
    '', '## 预期结果', ...item.expected.map(text => `- ${text}`),
    '', '由 AxisMeld 公开测试门户生成；由提交者确认后公开提交。',
  ].join('\n');
  const title = `[测试反馈] ${item.id} · ${result}`;
  const repo = publicUrl(config.repoUrl, true);
  let url = null;
  if (config.feedback?.mode === 'github' && repo && /^\/[^/]+\/[^/]+\/?$/.test(repo.pathname)) {
    url = new URL(`${repo.origin}${repo.pathname.replace(/\/$/, '')}/issues/new`);
    url.searchParams.set('title', title);
    url.searchParams.set('body', body);
    url.searchParams.set('labels', asText(config.feedback.label, 'test-feedback'));
  } else if (config.feedback?.mode === 'external') {
    url = publicUrl(config.feedback.externalUrl);
  }
  const long = Boolean(url && config.feedback?.mode === 'github' && url.href.length > 7000);
  // Keep the complete body in the preview/copy field. A short link avoids sending
  // an oversized request; the visitor explicitly pastes the body on GitHub.
  if (long) url.searchParams.delete('body');
  return { body, title, url: url?.href || null, long };
}

function element(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

async function boot() {
  const byId = id => document.getElementById(id);
  let config;
  let items;
  try {
    const responses = await Promise.all(['config.json', 'catalog.json'].map(async path => {
      const response = await fetch(new URL(`./${path}`, document.baseURI), { cache: 'no-cache', credentials: 'omit' });
      if (!response.ok) throw new Error(`${path} 加载失败（${response.status}）。`);
      return response.json();
    }));
    config = responses[0];
    items = normalizeCatalog(responses[1]);
  } catch (error) {
    byId('loading-state').hidden = true;
    byId('load-error').hidden = false;
    byId('load-error').textContent = `${error.message} 请刷新页面重试；已有本浏览器记录不会被清除。`;
    return;
  }

  const buildId = asText(config.buildId, '未指定构建');
  const repo = publicUrl(config.repoUrl, true);
  const release = publicUrl(config.releaseUrl, true);
  const feedbackList = publicUrl(config.feedback?.listUrl, config.feedback?.mode === 'github');
  const link = (id, url) => {
    const node = byId(id);
    node.hidden = !url;
    if (url) node.href = url.href;
  };
  if (repo) {
    const readme = new URL(repo.href);
    readme.hash = 'readme';
    link('readme-link', readme);
    const source = new URL(`${repo.origin}${repo.pathname.replace(/\/$/, '')}/tree/${asText(config.sourceBranch, 'main').split('/').map(encodeURIComponent).join('/')}`);
    link('source-link', source);
    const roadmap = new URL(`${repo.origin}${repo.pathname.replace(/\/$/, '')}/blob/${asText(config.sourceBranch, 'main').split('/').map(encodeURIComponent).join('/')}/docs/ROADMAP.md`);
    link('roadmap-link', roadmap);
  }
  link('download-link', release);
  byId('download-pending').hidden = Boolean(release);
  link('feedback-list-link', feedbackList);
  byId('published-build').textContent = buildId;
  if (config.feedback?.mode !== 'github') {
    document.querySelector('.privacy-notice p').textContent = '本浏览器记录 ≠ 已提交维护者。勾选与备注只保存在这里，不会自动上传或跨设备同步。请通过公开反馈入口另行提交。';
  }

  let state;
  const storageWarning = message => {
    byId('storage-warning').textContent = message;
    byId('storage-warning').hidden = false;
    byId('save-status').textContent = '当前记录未能持久保存，请导出备份';
  };
  let savedRaw = null;
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored) savedRaw = JSON.parse(stored);
  } catch {
    storageWarning('无法读取本浏览器记录。页面仍可使用；原存储内容不会在载入时被清除。请将本次记录导出 JSON 备份。');
  }
  state = normalizeState(savedRaw, buildId);
  function save() {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify({ ...state, updatedAt: new Date().toISOString() }));
      byId('storage-warning').hidden = true;
      byId('save-status').textContent = '已保存在本浏览器 · 尚未提交维护者';
    } catch {
      storageWarning('浏览器未允许保存，或可用存储空间不足。当前操作只保留在本次页面内；关闭前请导出 JSON 备份。');
    }
  }
  function updateRecord(id, patch) {
    state.records[id] = { ...recordFor(state, id), ...patch, updatedAt: new Date().toISOString() };
    save();
  }

  const filters = { query: '', status: 'all', group: '', recent: false, history: false };
  let page = 1;
  const openItems = new Set();
  const activeItems = items.filter(item => !item.superseded);
  const newCount = items.filter(item => item.isNew && !item.superseded).length;
  const historyCount = items.length - activeItems.length;
  byId('catalog-summary').textContent = `${activeItems.length} 项当前测试 · ${historyCount} 项历史记录`;
  byId('count-new').textContent = String(newCount);
  byId('count-history').textContent = historyCount ? `(${historyCount})` : '';
  byId('recent-toggle').disabled = newCount === 0;
  byId('history-toggle').disabled = historyCount === 0;
  for (const group of [...new Set(items.map(item => item.group))]) {
    const option = element('option', '', group);
    option.value = group;
    byId('group-filter').append(option);
  }
  byId('default-build').value = state.defaultBuildId;
  byId('default-build').addEventListener('change', event => {
    state.defaultBuildId = event.target.value.trim().slice(0, 120) || buildId;
    event.target.value = state.defaultBuildId;
    save();
    // Updating the default never overwrites previously recorded item versions.
    for (const input of document.querySelectorAll('[data-record-build]')) {
      if (!own(state.records, input.dataset.recordBuild)) input.value = state.defaultBuildId;
    }
  });

  function renderStats() {
    const counts = { all: activeItems.length, untested: 0, tested: 0, passed: 0, failed: 0 };
    for (const item of activeItems) {
      const status = recordFor(state, item.id).status;
      if (status === 'untested') counts.untested++;
      else {
        counts.tested++;
        if (status === 'passed' || status === 'failed') counts[status]++;
      }
    }
    for (const [key, count] of Object.entries(counts)) byId(`count-${key}`).textContent = String(count);
    for (const button of document.querySelectorAll('[data-filter]')) {
      const active = button.dataset.filter === filters.status;
      button.classList.toggle('active', active);
      button.setAttribute('aria-pressed', String(active));
    }
  }

  const dialog = byId('feedback-dialog');
  function openFeedback(item) {
    const draft = feedbackDraft(config, item, recordFor(state, item.id));
    byId('feedback-title').textContent = `创建公开反馈 · ${item.id}`;
    byId('feedback-body').value = draft.body;
    byId('copy-status').textContent = '';
    byId('long-feedback-warning').hidden = !draft.long;
    const target = byId('submit-feedback-link');
    target.hidden = !draft.url;
    if (draft.url) target.href = draft.url;
    target.textContent = config.feedback?.mode === 'external' ? '打开反馈表单 ↗' : draft.long ? '去 GitHub 粘贴提交 ↗' : '去 GitHub 确认提交 ↗';
    byId('feedback-instructions').textContent = config.feedback?.mode === 'external'
      ? '请先复制正文，再到公开反馈表单粘贴并提交。请移除私人信息；此页面不会自动提交。'
      : '以下内容会公开展示。请移除私人信息；继续后需要登录 GitHub，并在 Issue 页面确认提交。';
    if (!draft.url) byId('feedback-instructions').textContent = '公开反馈入口暂不可用。请复制完整正文或导出 JSON，稍后通过项目反馈入口提交。';
    dialog.showModal();
  }
  byId('close-dialog').addEventListener('click', () => dialog.close());
  dialog.addEventListener('click', event => { if (event.target === dialog) { const r = dialog.getBoundingClientRect(); if (event.clientX < r.left || event.clientX > r.right || event.clientY < r.top || event.clientY > r.bottom) dialog.close(); } });
  byId('copy-feedback').addEventListener('click', async () => {
    try {
      await navigator.clipboard.writeText(byId('feedback-body').value);
      byId('copy-status').textContent = '已复制完整正文；尚未提交。';
    } catch {
      byId('feedback-body').focus();
      byId('feedback-body').select();
      byId('copy-status').textContent = '浏览器未允许自动复制。正文已选中，请按 Ctrl+C 或使用系统复制。';
    }
  });

  function instructionBlock(title, values, ordered) {
    const block = element('div');
    block.append(element('h4', '', title));
    if (values.length) {
      const list = element(ordered ? 'ol' : 'ul');
      values.forEach(value => list.append(element('li', '', value)));
      block.append(list);
    } else block.append(element('p', 'no-text', '详见项目说明。'));
    return block;
  }

  function testCard(item) {
    const record = recordFor(state, item.id);
    const card = element('article', `test-card${item.superseded ? ' history-card' : ''}`);
    card.dataset.testId = item.id;
    const row = element('div', 'test-row');
    const heading = element('div', 'test-heading');
    heading.append(element('span', 'test-number', item.id));
    const titleCopy = element('div', 'title-copy');
    const titleLine = element('div', 'title-line');
    const title = element('h3', 'test-title', item.title);
    title.id = `title-${item.id}`;
    titleLine.append(title);
    if (item.isNew) titleLine.append(element('span', 'new-badge', '新增'));
    if (item.superseded) titleLine.append(element('span', 'history-badge', '历史条目'));
    const meta = element('div', 'test-meta');
    meta.append(element('span', '', item.group));
    if (item.maintainerStatus && !['pending', 'untested'].includes(item.maintainerStatus)) {
      meta.append(element('span', 'maintainer-history', `维护者历史：${HISTORY_STATUS[item.maintainerStatus]}`));
    }
    titleCopy.append(titleLine, meta);
    heading.append(titleCopy);
    row.append(heading);
    const statusLabel = element('label', 'status-field');
    statusLabel.append(element('span', 'sr-only', `${item.id} 的本浏览器测试状态`));
    const statusSelect = element('select');
    statusSelect.dataset.status = record.status;
    statusSelect.dataset.recordStatus = item.id;
    for (const [key, label] of Object.entries(STATUS)) {
      const option = element('option', '', label);
      option.value = key;
      statusSelect.append(option);
    }
    statusSelect.value = record.status;
    statusSelect.addEventListener('change', event => {
      updateRecord(item.id, { status: event.target.value });
      statusSelect.dataset.status = event.target.value;
      renderStats();
      renderList();
    });
    statusLabel.append(statusSelect);
    row.append(statusLabel);
    card.append(row);

    const details = element('details');
    details.open = openItems.has(item.id);
    details.addEventListener('toggle', () => { if (details.open) openItems.add(item.id); else openItems.delete(item.id); });
    details.append(element('summary', '', '操作步骤 / 预期结果 / 记录反馈'));
    const detail = element('div', 'test-detail');
    if (item.superseded) detail.append(element('p', 'history-notice', '历史条目：此入口或设计已调整，保留原始测试记录供追溯，不作为当前构建的验收要求。'));
    const instructions = element('div', 'test-instructions');
    instructions.append(instructionBlock('操作步骤', item.steps, true), instructionBlock('预期结果', item.expected, false));
    detail.append(instructions);
    const noteRow = element('div', 'note-row');
    const noteLabel = element('label', 'note-label', '我的备注 · 仅保存在本浏览器');
    noteLabel.htmlFor = `note-${item.id}`;
    const noteCount = element('span', 'note-count', `${record.note.length} / ${NOTE_LIMIT}`);
    noteRow.append(noteLabel, noteCount);
    const note = element('textarea', 'test-note');
    note.id = `note-${item.id}`;
    note.maxLength = NOTE_LIMIT;
    note.rows = 2;
    note.placeholder = '记录实际结果、复现步骤或不符合预期的地方…';
    note.value = record.note;
    note.addEventListener('input', () => {
      updateRecord(item.id, { note: note.value });
      noteCount.textContent = `${note.value.length} / ${NOTE_LIMIT}`;
    });
    detail.append(noteRow, note);
    const recordFooter = element('div', 'record-footer');
    const recordBuild = element('div', 'record-build');
    const versionLabel = element('label', 'record-build-label', '此项测试版本');
    versionLabel.htmlFor = `build-${item.id}`;
    const version = element('input');
    version.id = `build-${item.id}`;
    version.dataset.recordBuild = item.id;
    version.value = record.buildId;
    version.maxLength = 120;
    version.spellcheck = false;
    version.addEventListener('change', () => {
      version.value = version.value.trim() || state.defaultBuildId;
      updateRecord(item.id, { buildId: version.value });
    });
    recordBuild.append(versionLabel, version);
    const feedback = element('button', 'secondary-button', '创建公开反馈 ↗');
    feedback.type = 'button';
    feedback.dataset.feedbackId = item.id;
    feedback.addEventListener('click', () => openFeedback(item));
    recordFooter.append(recordBuild, feedback);
    detail.append(recordFooter);
    const recordedDate = record.updatedAt && !Number.isNaN(Date.parse(record.updatedAt)) ? new Date(record.updatedAt).toLocaleString('zh-CN', { hour12: false }) : null;
    detail.append(element('p', 'record-meta', recordedDate ? `上次本地记录：${recordedDate} · 尚未自动提交维护者` : '选择状态或填写备注后自动保存。已测试包含通过、失败和未判定。'));
    details.append(detail);
    card.append(details);
    return card;
  }

  function renderList() {
    const matched = filterItems(items, state, filters);
    const pages = Math.max(1, Math.ceil(matched.length / PAGE_SIZE));
    page = Math.max(1, Math.min(page, pages));
    const offset = (page - 1) * PAGE_SIZE;
    const nodes = matched.slice(offset, offset + PAGE_SIZE).map(testCard);
    byId('test-list').replaceChildren(...nodes);
    byId('empty-state').hidden = matched.length !== 0;
    byId('pagination').hidden = matched.length === 0;
    byId('page-label').textContent = `${page} / ${pages} 页`;
    byId('previous-page').disabled = page === 1;
    byId('next-page').disabled = page === pages;
    const historical = matched.filter(item => item.superseded).length;
    const range = matched.length ? `${offset + 1}–${Math.min(offset + PAGE_SIZE, matched.length)}` : '0';
    byId('results-summary').textContent = `显示 ${range} / ${matched.length} 项${historical ? ` · 含 ${historical} 项历史` : ''}`;
    byId('recent-toggle').setAttribute('aria-pressed', String(filters.recent));
    byId('clear-filters').hidden = !filters.query && !filters.group && filters.status === 'all' && !filters.recent && !filters.history;
  }

  function changed() { page = 1; renderStats(); renderList(); }
  byId('search-input').addEventListener('input', event => { filters.query = event.target.value; changed(); });
  byId('group-filter').addEventListener('change', event => { filters.group = event.target.value; changed(); });
  byId('history-toggle').addEventListener('change', event => { filters.history = event.target.checked; changed(); });
  byId('recent-toggle').addEventListener('click', () => { filters.recent = !filters.recent; changed(); });
  for (const button of document.querySelectorAll('[data-filter]')) button.addEventListener('click', () => { filters.status = button.dataset.filter; changed(); });
  byId('clear-filters').addEventListener('click', () => {
    Object.assign(filters, { query: '', group: '', status: 'all', recent: false, history: false });
    byId('search-input').value = '';
    byId('group-filter').value = '';
    byId('history-toggle').checked = false;
    changed();
  });
  const turnPage = delta => {
    page += delta;
    renderList();
    byId('test-list').scrollIntoView({ behavior: 'instant', block: 'start' });
    byId('test-list').focus({ preventScroll: true });
  };
  byId('previous-page').addEventListener('click', () => turnPage(-1));
  byId('next-page').addEventListener('click', () => turnPage(1));
  byId('export-button').addEventListener('click', () => {
    const payload = {
      schemaVersion: 1, exportedAt: new Date().toISOString(), project: asText(config.projectName, 'AxisMeld'),
      publishedBuildId: buildId, defaultBuildId: state.defaultBuildId,
      storageScope: 'this-browser-only', submittedToMaintainer: false,
      records: state.records,
    };
    const blob = new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const anchor = element('a');
    anchor.href = url;
    anchor.download = `axismeld-test-records-${new Date().toISOString().slice(0, 10)}.json`;
    document.body.append(anchor);
    anchor.click();
    anchor.remove();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
    byId('save-status').textContent = '已请求下载 JSON 备份 · 尚未提交维护者';
  });

  renderStats();
  renderList();
  byId('workspace').hidden = false;
  byId('loading-state').hidden = true;
  document.documentElement.dataset.ready = 'true';
}

if (typeof document !== 'undefined') boot();
