import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { test } from 'node:test';
import { runInNewContext } from 'node:vm';
const source = readFileSync(new URL('../../static/js/theme.js', import.meta.url), 'utf8');

function harness({ time = '12:00', stored = null, blocked = false, reduced = true, dial = null, imageSupport = false } = {}) {
  const styles = new Map();
  const tokens = new Map([...readFileSync(new URL('../../static/css/tokens.css', import.meta.url), 'utf8').matchAll(/(--clock-[\w-]+):\s*([^;]+);/g)].map(m => [m[1], m[2]]));
  const root = { dataset: {}, style: { setProperty: (key, value) => styles.set(key, value) } };
  const events = new Map();
  const documentEvents = new Map();
  const state = { stored, time };
  const pictures = [];
  const meta = { dataset: { light: '#f8fafc', dark: '#0c1424' } };
  const document = {
    documentElement: root, readyState: 'complete', hidden: false,
    querySelector: s => s.includes('theme-color') ? meta : null,
    querySelectorAll: s => s === '[data-clock-picture]' ? pictures : s === '[data-clock-dial]' && dial ? [dial] : [],
    addEventListener: (name, fn) => documentEvents.set(name, fn),
  };
  const pendingImages = [];
  if (imageSupport) document.createElement = () => ({
    style: {}, setAttribute() {}, append(img) { this.img = img; }, querySelector() { return this.img; },
  });
  const frames = new Map();
  let nextFrame = 0;
  const window = {
    getComputedStyle: () => ({ getPropertyValue: key => tokens.get(key) || '' }),
    requestAnimationFrame: fn => { const id = ++nextFrame; frames.set(id, fn); return id; },
    cancelAnimationFrame: id => frames.delete(id),
    sessionStorage: {
      getItem() { if (blocked) throw Error('blocked'); return state.stored; },
      setItem(k, v) { if (blocked) throw Error('blocked'); state.stored = v; },
      removeItem() { if (blocked) throw Error('blocked'); state.stored = null; },
    },
    addEventListener: (name, fn) => events.set(name, fn),
    setInterval: fn => events.set('tick', fn),
    matchMedia: () => ({ matches: reduced }),
  };
  if (imageSupport) window.Image = class { set src(value) { pendingImages.push({ url: value, image: this }); } };
  class ClockDate {
    getHours() { return Number(state.time.slice(0, 2)); }
    getMinutes() { return Number(state.time.slice(3)); }
  }
  runInNewContext(source, { window, document, Date: ClockDate });
  const flush = (count = 180) => { for (let i = 0; i < count && frames.size; i++) { const batch = [...frames.values()]; frames.clear(); batch.forEach(fn => fn(i * 16)); } };
  return { clock: window.TabloClock, root, state, events, documentEvents, pictures, meta, styles, flush, frames, pendingImages };
}

for (const [time, phase] of [
  ['00:00', 'night', 'dark'], ['05:59', 'night', 'dark'],
  ['06:00', 'morning', 'light'], ['09:59', 'morning', 'light'],
  ['10:00', 'day', 'light'], ['16:59', 'day', 'light'],
  ['17:00', 'sunset', 'dark'], ['19:59', 'sunset', 'dark'],
  ['20:00', 'night', 'dark'], ['23:59', 'night', 'dark'],
]) {
  test(`local ${time} resolves ${phase} before content renders`, () => {
    const h = harness({ time });
    assert.equal(h.root.dataset.dayPhase, phase);
    assert.ok(['dark', 'light'].includes(h.root.dataset.theme));
    assert.equal(h.meta.content, h.styles.get('--color-bg'));
  });
}

test('manual time stays fixed across ticks and reloads, real time clears it', () => {
  const h = harness();
  h.clock.setTime('21:15');
  assert.equal(h.state.stored, '21:15');
  h.state.time = '08:00';
  h.events.get('tick')();
  assert.equal(h.root.dataset.dayPhase, 'night');
  assert.equal(harness({ stored: h.state.stored }).root.dataset.dayPhase, 'night');
  h.clock.useRealTime();
  assert.equal(h.state.stored, null);
  assert.equal(h.root.dataset.dayPhase, 'morning');
});

test('new tab, invalid storage and disabled storage use local time', () => {
  for (const stored of [null, 'dark', '25:00', '21:99', '9:30']) {
    assert.equal(harness({ time: '08:00', stored }).root.dataset.dayPhase, 'morning');
  }
  const h = harness({ blocked: true });
  h.clock.setTime('18:30');
  assert.equal(h.root.dataset.dayPhase, 'sunset');
  h.clock.setTime('bad');
  assert.equal(h.root.dataset.dayPhase, 'sunset');
  h.clock.useRealTime();
  assert.equal(h.root.dataset.dayPhase, 'day');
});

test('timer, visibility and pageshow catch up to the real local time', () => {
  const h = harness({ time: '16:59' });
  h.state.time = '17:00'; h.events.get('tick')();
  assert.equal(h.root.dataset.dayPhase, 'sunset');
  h.state.time = '20:00'; h.documentEvents.get('visibilitychange')();
  assert.equal(h.root.dataset.dayPhase, 'night');
  h.state.time = '06:00'; h.events.get('pageshow')();
  assert.equal(h.root.dataset.dayPhase, 'morning');
});

function picture({ deferred = false } = {}) {
  const listeners = new Map();
  const source = { srcset: '', removeAttribute() { this.srcset = ''; } };
  const img = {
    dataset: deferred ? { src: '/original.webp' } : {},
    src: deferred ? '' : '/original.webp',
    getAttribute(k) { return this[k] || null; },
    addEventListener: (name, fn) => listeners.set(name, fn),
    cloneNode: () => ({ style: {}, removeAttribute() {} }),
  };
  const link = { href: '/original.webp' };
  const p = {
    dataset: { clockDefault: '/original.webp', clockNight: '/night.webp' },
    querySelector: s => s === 'source' ? source : img,
    closest: () => link,
    append(layer) { this.layer = layer; },
  };
  return { p, source, img, link, listeners };
}

test('pictures select only the requested variant and fall back on load error', () => {
  const h = harness({ time: '22:00' });
  const a = picture(), b = picture();
  h.pictures.push(a.p, b.p);
  h.clock.refreshImages();
  assert.equal(a.source.srcset, '/night.webp');
  assert.equal(b.source.srcset, a.source.srcset);
  assert.equal(a.link.href, '/night.webp');
  a.listeners.get('error')();
  assert.equal(a.source.srcset, '/original.webp');
  assert.equal(a.link.href, '/original.webp');
  h.clock.setTime('08:00');
  assert.equal(a.source.srcset, '/original.webp');
});

test('deferred lightbox media stays deferred and receives the selected URL', () => {
  const h = harness({ time: '22:00' });
  const a = picture({ deferred: true });
  h.pictures.push(a.p);
  h.clock.refreshImages();
  assert.equal(a.img.src, '');
  assert.equal(a.source.srcset, '');
  assert.equal(a.img.dataset.src, '/night.webp');
  a.img.src = a.img.dataset.src;
  h.clock.setTime('12:00');
  assert.equal(a.source.srcset, '/original.webp');
  assert.equal(a.img.dataset.src, '/original.webp');
});


test('an early variant failure falls back before DOMContentLoaded', () => {
  const h = harness({ time: '22:00' });
  const a = picture();
  a.img.tagName = 'IMG';
  a.img.closest = () => a.p;
  h.clock.prepare(a.p);
  assert.equal(a.source.srcset, '/night.webp');
  h.documentEvents.get('error')({ target: a.img });
  assert.equal(a.source.srcset, '/original.webp');
  assert.equal(a.img.src, '/original.webp');
});

test('the palette changes within a phase and stays continuous across its old boundaries', () => {
  const h = harness();
  h.clock.setTime('12:00');
  const noon = h.styles.get('--color-bg');
  h.clock.setTime('14:00');
  assert.notEqual(h.styles.get('--color-bg'), noon);
  const rgb = value => value.match(/[\d.]+/g).slice(0, 3).map(Number);
  for (const boundary of ['06:00', '10:00', '17:00', '20:00', '00:00']) {
    const minutes = Number(boundary.slice(0, 2)) * 60;
    const before = (minutes + 1439) % 1440;
    h.clock.setTime(`${String(Math.floor(before / 60)).padStart(2, '0')}:59`);
    const a = rgb(h.styles.get('--color-bg'));
    h.clock.setTime(boundary);
    const b = rgb(h.styles.get('--color-bg'));
    assert.ok(Math.max(...a.map((v, i) => Math.abs(v - b[i]))) < 4, boundary);
  }
});

test('all intermediate times keep readable foregrounds on every surface', () => {
  const h = harness();
  const rgb = value => value.match(/[\d.]+/g).slice(0, 3).map(Number);
  const lum = value => rgb(value).reduce((sum, c, i) => {
    c /= 255;
    return sum + (c <= .04045 ? c / 12.92 : ((c + .055) / 1.055) ** 2.4) * [.2126, .7152, .0722][i];
  }, 0);
  for (let minute = 0; minute < 1440; minute += 3) {
    h.clock.setTime(`${String(Math.floor(minute / 60)).padStart(2, '0')}:${String(minute % 60).padStart(2, '0')}`);
    for (const fg of ['--color-ink', '--color-muted', '--color-accent-text']) {
      for (const bg of ['--color-bg', '--color-surface', '--color-surface-2']) {
        const a = lum(h.styles.get(fg)), b = lum(h.styles.get(bg));
        assert.ok((Math.max(a, b) + .05) / (Math.min(a, b) + .05) >= 4.49, `${minute}: ${fg} on ${bg}`);
      }
    }
  }
});

test('smooth changes paint intermediate frames and reduced motion settles immediately', () => {
  const h = harness({ reduced: false });
  const start = h.styles.get('--color-bg');
  h.clock.setTime('22:00');
  assert.equal(h.styles.get('--color-bg'), start);
  h.flush(1);
  const middle = h.styles.get('--color-bg');
  assert.notEqual(middle, start);
  h.flush();
  assert.notEqual(h.styles.get('--color-bg'), middle);
  assert.equal(h.frames.size, 0);
  const reduced = harness({ reduced: true });
  reduced.clock.setTime('22:00');
  assert.equal(reduced.frames.size, 0);
  assert.equal(reduced.styles.get('--color-bg'), h.styles.get('--color-bg'));
});

function dialHarness(time = '23:55') {
  const events = new Map();
  const hands = {};
  for (const hand of ['hour', 'minute']) {
    const keyEvents = new Map();
    hands[hand] = { dataset: { clockHand: hand }, focus() {}, addEventListener: (n, fn) => keyEvents.set(n, fn), keyEvents };
  }
  const dial = {
    getBoundingClientRect: () => ({ x: 0, y: 0, width: 320, height: 320 }),
    addEventListener: (n, fn) => events.set(n, fn),
    querySelector: selector => hands[selector.includes('"hour"') ? 'hour' : 'minute'],
    querySelectorAll: () => Object.values(hands),
    setPointerCapture() {}, hasPointerCapture: () => false,
  };
  const h = harness({ time, dial });
  const pointer = (name, degrees, hand = 'minute') => {
    const angle = degrees * Math.PI / 180;
    events.get(name)({
      type: name, button: 0, isPrimary: true, pointerId: 1,
      clientX: 160 + Math.sin(angle) * 100, clientY: 160 - Math.cos(angle) * 100,
      target: { closest: () => hands[hand] }, preventDefault() {},
    });
  };
  return { ...h, pointer, hands, dialEvents: events };
}

test('minute drag crosses midnight and both directions without a full-circle jump', () => {
  const h = dialHarness();
  h.pointer('pointerdown', 330);
  h.pointer('pointermove', 30);
  h.pointer('pointerup', 30);
  assert.equal(h.state.stored, '00:05');
  h.pointer('pointerdown', 30);
  h.pointer('pointermove', 330);
  h.pointer('pointerup', 330);
  assert.equal(h.state.stored, '23:55');
});

test('hour drag follows multiple turns, carries minutes and handles pointer cancellation', () => {
  const h = dialHarness('11:30');
  h.pointer('pointerdown', 345, 'hour');
  for (const angle of [75, 165, 255, 345, 75]) h.pointer('pointermove', angle, 'hour');
  h.pointer('pointercancel', 75, 'hour');
  assert.equal(h.state.stored, '02:30');
  assert.equal(h.root.dataset.clockDragging, undefined);
});

test('keyboard hands, home/end and tap-to-move work without dragging', () => {
  const h = dialHarness('11:59');
  const key = (hand, value) => h.hands[hand].keyEvents.get('keydown')({ key: value, preventDefault() {} });
  key('minute', 'ArrowUp');
  assert.equal(h.state.stored, '12:00');
  key('hour', 'ArrowRight');
  assert.equal(h.state.stored, '13:00');
  key('hour', 'Home');
  assert.equal(h.state.stored, '00:00');
  key('minute', 'End');
  assert.equal(h.state.stored, '23:59');
  h.pointer('pointerdown', 90);
  h.pointer('pointerup', 90);
  assert.equal(h.state.stored, '00:15');
});

test('neighboring images blend by clock position after decoding, without loading all variants', async () => {
  const h = harness({ time: '15:00', reduced: false, imageSupport: true });
  const a = picture();
  a.p.dataset.clockDay = '/day.webp';
  a.p.dataset.clockSunset = '/sunset.webp';
  h.pictures.push(a.p);
  h.clock.refreshImages();
  assert.deepEqual(h.pendingImages.map(p => p.url), ['/day.webp', '/sunset.webp']);
  h.pendingImages.forEach(p => p.image.onload());
  await new Promise(resolve => setImmediate(resolve));
  assert.equal(a.source.srcset, '/day.webp');
  assert.equal(a.p.layer.img.src, '/sunset.webp');
  assert.equal(a.p.layer.style.opacity, '0.5');
  h.clock.setTime('16:00'); h.flush();
  assert.ok(Number(a.p.layer.style.opacity) > .7);
  assert.equal(h.pendingImages.length, 2);
});

test('slow image responses cannot overwrite a newer clock position', async () => {
  const h = harness({ time: '15:00', reduced: false, imageSupport: true });
  const a = picture();
  a.p.dataset.clockDay = '/day.webp';
  a.p.dataset.clockSunset = '/sunset.webp';
  h.pictures.push(a.p); h.clock.refreshImages();
  h.clock.setTime('22:00'); h.flush();
  h.pendingImages.forEach(p => p.image.onload());
  await new Promise(resolve => setImmediate(resolve));
  assert.equal(a.source.srcset, '/night.webp');
  assert.equal(a.p.layer, undefined);
});


test('a second pointer cannot take over an active hand gesture', () => {
  const h = dialHarness('12:00');
  h.pointer('pointerdown', 0);
  h.dialEvents.get('pointermove')({ pointerId: 2, clientX: 260, clientY: 160 });
  h.dialEvents.get('pointercancel')({ pointerId: 2 });
  assert.equal(h.root.dataset.clockDragging, 'true');
  h.pointer('pointermove', 90);
  h.pointer('pointerup', 90);
  assert.equal(h.state.stored, '12:15');
});

test('changing the hour does not spin the minute hand through whole revolutions', () => {
  const h = harness({ time: '12:15', reduced: false });
  const start = Number.parseFloat(h.styles.get('--clock-minute-angle'));
  h.clock.setTime('22:15'); h.flush(1);
  assert.equal(Number.parseFloat(h.styles.get('--clock-minute-angle')), start);
  h.flush();
  assert.equal(Number.parseFloat(h.styles.get('--clock-minute-angle')), start);
});
