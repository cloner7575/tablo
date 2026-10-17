import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { test } from 'node:test';
import { runInNewContext } from 'node:vm';
const source = readFileSync(new URL('../../static/js/theme.js', import.meta.url), 'utf8');

function harness({ stored = null, dark = false, blocked = false } = {}) {
  const root = { dataset: {} };
  const events = new Map();
  const attributes = new Map();
  const clicks = [];
  const button = { setAttribute: (k, v) => attributes.set(k, v), addEventListener: (k, fn) => clicks.push(fn) };
  const meta = { dataset: { light: '#f8fafc', dark: '#0c1424' }, content: '' };
  const media = { matches: dark, addEventListener: (k, fn) => events.set('preference', fn) };
  const state = { stored };
  const window = {
    matchMedia: () => media,
    localStorage: {
      getItem() { if (blocked) throw new Error('Storage disabled'); return state.stored; },
      setItem(k, v) { if (blocked) throw new Error('Storage disabled'); state.stored = v; },
    },
    addEventListener: (k, fn) => events.set(k, fn),
  };
  const document = { documentElement: root, readyState: 'complete', querySelector: () => meta, querySelectorAll: () => [button] };
  runInNewContext(source, { window, document });
  return { root, attributes, meta, state, events, media, click: () => clicks[0]() };
}

test('saved theme wins before content renders and toggle persists its inverse', () => {
  const h = harness({ stored: 'dark' });
  assert.equal(h.root.dataset.theme, 'dark');
  assert.equal(h.meta.content, '#0c1424');
  assert.equal(h.attributes.get('aria-pressed'), 'true');
  h.click();
  assert.equal(h.root.dataset.theme, 'light');
  assert.equal(h.state.stored, 'light');
  assert.equal(h.attributes.get('aria-pressed'), 'false');
});

test('device preference is followed until the visitor explicitly chooses', () => {
  const h = harness();
  h.media.matches = true;
  h.events.get('preference')();
  assert.equal(h.root.dataset.theme, 'dark');
  h.click();
  h.events.get('preference')();
  assert.equal(h.root.dataset.theme, 'light');
});

test('disabled storage still permits accessible theme changes', () => {
  const h = harness({ blocked: true, dark: true });
  h.click();
  assert.equal(h.root.dataset.theme, 'light');
  assert.match(h.attributes.get('aria-label'), /تاریک/);
});

test('a theme change in another tab is reflected without reloading', () => {
  const h = harness();
  h.events.get('storage')({ key: 'tablo-theme', newValue: 'dark' });
  assert.equal(h.root.dataset.theme, 'dark');
  h.events.get('storage')({ key: 'tablo-theme', newValue: null });
  assert.equal(h.root.dataset.theme, 'light');
});
