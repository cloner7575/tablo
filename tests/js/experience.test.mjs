import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { test } from 'node:test';
import { runInNewContext } from 'node:vm';

const source = readFileSync(new URL('../../static/js/experience.js', import.meta.url), 'utf8');

function harness({ reduced = false, supported = true, reading = false, ambient = false, photograph = false } = {}) {
  const preferences = { matches: reduced, listeners: [], addEventListener(name, fn) { this.listeners.push(fn); } };
  const animations = [];
  const targets = [0, 1].map(() => ({
    dataset: {}, style: {},
    matches() { return photograph; },
    animate(frames, options) {
      const listeners = new Map();
      const animation = {
        cancelled: false, frames, options,
        addEventListener(name, fn) { listeners.set(name, fn); },
        cancel() { this.cancelled = true; listeners.get('cancel')?.(); },
      };
      animations.push(animation);
      return animation;
    },
  }));
  const observers = [];
  class Observer {
    constructor(fn) { this.callback = fn; this.targets = new Set(); observers.push(this); }
    observe(el) { this.targets.add(el); }
    unobserve(el) { this.targets.delete(el); }
    disconnect() { this.targets.clear(); }
  }
  const progress = { style: {} };
  const bounds = { top: 1600, height: 2000 };
  const documentEvents = new Map();
  const scene = { dataset: {} };
  const document = {
    readyState: 'complete', hidden: false, documentElement: { dataset: {} },
    querySelectorAll(selector) { return selector.includes('.at-hero__copy') ? targets : []; },
    addEventListener(name, fn) { documentEvents.set(name, fn); },
    querySelector(selector) {
      if (selector === '[data-ambient-motion]') return ambient ? scene : null;
      if (!reading) return null;
      if (selector === '[data-reading-progress] span') return progress;
      if (selector === '.ed-article-body') return { getBoundingClientRect: () => bounds };
      if (selector === '.site-header') return { getBoundingClientRect: () => ({ height: 68 }) };
      return null;
    },
  };
  const events = new Map();
  const window = {
    location: { pathname: '/', href: 'https://demo.invalid/' }, innerHeight: 800,
    IntersectionObserver: supported ? Observer : undefined,
    matchMedia(query) { return query.includes('reduced-motion') ? preferences : { matches: false, addEventListener() {} }; },
    addEventListener(name, fn) { events.set(name, fn); },
    requestAnimationFrame(fn) { fn(); },
  };
  runInNewContext(source, { document, window, URL, IntersectionObserver: Observer });
  const changePreference = (value) => {
    preferences.matches = value;
    preferences.listeners.forEach((fn) => fn({ matches: value }));
  };
  const enter = (target, observer = observers.at(-1)) => observer.callback([{ target, isIntersecting: true }]);
  return { targets, animations, observers, document, enter, changePreference, events, progress, bounds, scene, documentEvents };
}

test('reduced motion never hides content or starts an observer/animation', () => {
  const h = harness({ reduced: true });
  assert.equal(h.observers.length, 0);
  assert.equal(h.animations.length, 0);
  assert.equal(h.document.documentElement.dataset.motion, 'reduced');
  assert.deepEqual(h.targets.map((el) => el.style), [{}, {}]);
});

test('content stays visible before observation and reveals only once', () => {
  const h = harness();
  assert.equal(h.animations.length, 0);
  assert.deepEqual(h.targets[0].style, {});
  h.enter(h.targets[0]);
  h.enter(h.targets[0]);
  assert.equal(h.animations.length, 1);
  assert.equal(h.animations[0].frames.at(-1).opacity, 1);
});

test('preference changes cancel active motion and can resume unvisited content', () => {
  const h = harness();
  h.enter(h.targets[0]);
  h.changePreference(true);
  assert.equal(h.animations[0].cancelled, true);
  assert.equal(h.observers[0].targets.size, 0);
  h.changePreference(false);
  h.enter(h.targets[1]);
  h.enter(h.targets[0]);
  assert.equal(h.animations.length, 2);
});

test('missing observer API falls back to readable static content', () => {
  const h = harness({ supported: false });
  assert.equal(h.observers.length, 0);
  assert.equal(h.animations.length, 0);
  assert.deepEqual(h.targets[0].style, {});
});

test('photograph entrances settle without layout animation and stop on reduced motion', () => {
  const h = harness({ photograph: true });
  h.enter(h.targets[0]);
  const animation = h.animations[0];
  assert.equal(animation.frames.at(-1).scale, '1');
  assert.equal(animation.frames.at(-1).translate, '0 0');
  assert.ok(animation.options.duration < 1000);
  assert.ok(animation.frames.every(frame => !('width' in frame) && !('height' in frame)));
  h.changePreference(true);
  assert.ok(animation.cancelled);
  h.enter(h.targets[1]);
  assert.equal(h.animations.length, 1);
});

test('reading progress is clamped to the article body even with reduced motion', () => {
  const h = harness({ reading: true, reduced: true });
  assert.equal(h.progress.style.transform, 'scaleX(0)');
  h.bounds.top = -1600;
  h.events.get('scroll')();
  assert.equal(h.progress.style.transform, 'scaleX(1)');
  assert.equal(h.animations.length, 0);
});

test('ambient motion runs only on screen and pauses when the page is hidden', () => {
  const h = harness({ ambient: true });
  assert.equal(h.scene.dataset.ambient, 'paused');
  h.enter(h.scene);
  assert.equal(h.scene.dataset.ambient, 'running');
  h.document.hidden = true;
  h.documentEvents.get('visibilitychange')();
  assert.equal(h.scene.dataset.ambient, 'paused');
  h.document.hidden = false;
  h.documentEvents.get('visibilitychange')();
  assert.equal(h.scene.dataset.ambient, 'running');
  h.observers.at(-1).callback([{ target: h.scene, isIntersecting: false }]);
  assert.equal(h.scene.dataset.ambient, 'paused');
});

test('ambient motion stays static without observer support or with reduced motion', () => {
  for (const options of [{ supported: false }, { reduced: true }]) {
    const h = harness({ ambient: true, ...options });
    assert.equal(h.scene.dataset.ambient, 'paused');
  }
});

test('enabling motion after a reduced-motion load still waits for visibility', () => {
  const h = harness({ ambient: true, reduced: true });
  h.changePreference(false);
  assert.equal(h.scene.dataset.ambient, 'paused');
  h.enter(h.scene);
  assert.equal(h.scene.dataset.ambient, 'running');
});
