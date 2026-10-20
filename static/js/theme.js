/* The visitor's local clock controls continuous daylight, never server dates. */
(() => {
  const key = 'tablo-clock-time';
  const root = document.documentElement;
  const preference = window.matchMedia('(prefers-reduced-motion: reduce)');
  const css = window.getComputedStyle(root);
  const token = name => css.getPropertyValue(name).trim();
  const rgb = text => text.startsWith('#')
    ? [1, 3, 5].map(i => parseInt(text.slice(i, i + 2), 16))
    : text.match(/[\d.]+/g).slice(0, 3).map(Number);
  const white = rgb(token('--clock-white'));
  const black = rgb(token('--clock-black'));
  const mix = (a, b, t) => a.map((v, i) => v + (b[i] - v) * t);
  const color = a => `rgb(${a.map(v => v.toFixed(2)).join(' ')})`;
  const luminance = a => a.reduce((sum, v, i) => {
    const n = v / 255;
    return sum + (n <= .04045 ? n / 12.92 : ((n + .055) / 1.055) ** 2.4) * [.2126, .7152, .0722][i];
  }, 0);
  const contrast = (a, b) => (Math.max(luminance(a), luminance(b)) + .05) / (Math.min(luminance(a), luminance(b)) + .05);
  const clamp = value => Math.max(0, Math.min(1, value));
  const wrap = minutes => (minutes % 1440 + 1440) % 1440;
  const smooth = t => t * t * (3 - 2 * t);
  const stops = [0, 240, 330, 390, 480, 720, 900, 1020, 1080, 1140, 1200, 1320, 1440];
  const skies = stops.map(minute => rgb(token(`--clock-sky-${minute}`)));
  const dayAccent = rgb(token('--clock-day-accent'));
  const nightAccent = rgb(token('--clock-night-accent'));
  const warmAccent = rgb(token('--clock-warm-accent'));
  const coolAccent = rgb(token('--clock-cool-accent'));
  const labels = { morning: 'صبح', day: 'روز', sunset: 'غروب', night: 'شب' };
  const valid = value => typeof value === 'string' && /^(?:[01]\d|2[0-3]):[0-5]\d$/.test(value);
  const read = () => {
    try { const value = window.sessionStorage.getItem(key); return valid(value) ? value : null; }
    catch { return null; }
  };
  const fa = text => text.replace(/\d/g, digit => '۰۱۲۳۴۵۶۷۸۹'[digit]);
  const parse = value => Number(value.slice(0, 2)) * 60 + Number(value.slice(3));
  const format = minutes => {
    const m = Math.floor(wrap(minutes));
    return `${String(Math.floor(m / 60)).padStart(2, '0')}:${String(m % 60).padStart(2, '0')}`;
  };
  const localMinutes = () => { const date = new Date(); return date.getHours() * 60 + date.getMinutes(); };
  const phaseFor = minutes => minutes < 360 || minutes >= 1200 ? 'night' : minutes < 600 ? 'morning' : minutes < 1020 ? 'day' : 'sunset';
  let manual = read();
  let target = manual ? parse(manual) : localMinutes();
  let visual = target;
  let hourAngle = target / 2;
  let minuteAngle = target * 6;
  const cyclicDelta = (to, from, period) => (((to - from) % period + period * 1.5) % period) - period / 2;
  let frame = null;
  let lastFrame = null;
  let dragging = false;
  let painting = false;
  const failures = new WeakMap();
  const pictureStates = new WeakMap();
  const loadedImages = new Map();

  function palette(minutes) {
    const m = wrap(minutes);
    const i = Math.max(0, stops.findIndex(value => value > m) - 1);
    const t = smooth((m - stops[i]) / (stops[i + 1] - stops[i]));
    const bg = mix(skies[i], skies[i + 1], t);
    const light = clamp((luminance(bg) - .1) / .65);
    let surface = mix(bg, white, .035 + .55 * light);
    let surface2 = mix(bg, white, .065 * (1 - light));
    const score = ink => Math.min(...[bg, surface, surface2].map(b => contrast(ink, b)));
    let ink = score(black) > score(white) ? black : white;
    // At dusk, contract surface differences briefly so text stays >= 4.5:1.
    if (score(ink) < 4.5) { surface = bg; surface2 = bg; ink = contrast(black, bg) > contrast(white, bg) ? black : white; }
    const backgrounds = [bg, surface, surface2];
    const readable = (candidate, ratio = 4.5) => {
      let result = candidate;
      for (let n = 0; n < 10 && Math.min(...backgrounds.map(b => contrast(result, b))) < ratio; n++) result = mix(result, ink, .35);
      return Math.min(...backgrounds.map(b => contrast(result, b))) >= ratio ? result : ink;
    };
    const muted = readable(mix(ink, bg, .22));
    const accent = readable(mix(nightAccent, dayAccent, light));
    const warmth = Math.exp(-(((m - 1065) / 100) ** 2));
    const secondaryAccent = readable(mix(coolAccent, warmAccent, warmth));
    let accentSoft = mix(bg, accent, .08);
    if (contrast(accent, accentSoft) < 4.5) accentSoft = bg;
    const values = {
      '--color-bg': bg, '--color-bg-subtle': surface2, '--color-surface': surface,
      '--color-surface-2': surface2, '--color-stage': mix(bg, accent, .055),
      '--color-ink': ink, '--color-ink-soft': readable(mix(ink, bg, .08)),
      '--color-muted': muted, '--color-secondary': ink, '--color-secondary-ink': ink,
      '--color-secondary-soft': surface2, '--color-accent': accent,
      '--color-accent-text': accent, '--color-accent-hover': readable(mix(accent, ink, .15)),
      '--color-accent-soft': accentSoft, '--color-accent-line': mix(bg, accent, .3),
      '--color-accent-2': secondaryAccent, '--color-border': mix(bg, ink, .16),
      '--color-border-strong': mix(bg, ink, .32), '--color-code-bg': surface2,
      '--color-code-ink': ink, '--color-info': accent, '--color-info-bg': mix(bg, accent, .08),
    };
    for (const [name, value] of Object.entries(values)) root.style.setProperty(name, color(value));
    root.style.setProperty('--color-glass', `rgb(${bg.map(v => v.toFixed(2)).join(' ')} / .94)`);
    root.style.setProperty('--scene-brightness', (.95 + .07 * light).toFixed(4));
    root.style.setProperty('--scene-warmth', (.075 * warmth).toFixed(4));
    root.style.setProperty('--scene-saturation', (1 + .06 * warmth).toFixed(4));
    root.dataset.theme = luminance(bg) < .19 ? 'dark' : 'light';
    const meta = document.querySelector('meta[name="theme-color"]');
    if (meta) meta.content = color(bg);
  }

  const imageStops = [[0, 'night'], [480, 'morning'], [720, 'day'], [1080, 'sunset'], [1320, 'night'], [1440, 'night']];
  function imagePair(picture) {
    const m = wrap(visual);
    const index = Math.max(0, imageStops.findIndex(([minute]) => minute > m) - 1);
    const [start, first] = imageStops[index];
    const [end, second] = imageStops[index + 1];
    const url = phase => {
      const variant = picture.dataset[`clock${phase[0].toUpperCase()}${phase.slice(1)}`];
      return variant && !failures.get(picture)?.has(variant) ? variant : picture.dataset.clockDefault;
    };
    if (picture.dataset.clockExposure === 'single') {
      const selected = url(phaseFor(m));
      return { first: selected, second: selected, weight: 0 };
    }
    return { first: url(first), second: url(second), weight: smooth((m - start) / (end - start)) };
  }
  const prepare = picture => {
    const source = picture.querySelector('source');
    if (source && !picture.dataset.clockDeferred) {
      const pair = imagePair(picture);
      source.srcset = pair.weight >= .5 ? pair.second : pair.first;
    }
  };
  const load = url => {
    if (!loadedImages.has(url)) {
      loadedImages.set(url, new Promise(resolve => {
        const image = new window.Image();
        image.onload = () => {
          if (image.decode) image.decode().then(() => resolve(true), () => resolve(true));
          else resolve(true);
        };
        image.onerror = () => resolve(false);
        image.src = url;
      }));
    }
    return loadedImages.get(url);
  };
  function fadePrevious(picture, img, layer) {
    if (preference.matches || !picture.isConnected || !img.complete || !img.naturalWidth) return;
    // Retain the old composed exposure until the next decoded pair has faded in.
    const snapshot = document.createElement('span');
    snapshot.className = 'clock-image-snapshot';
    snapshot.setAttribute('aria-hidden', 'true');
    const previous = img.cloneNode(false);
    previous.removeAttribute('data-src'); previous.removeAttribute('fetchpriority');
    previous.src = img.currentSrc || img.src; previous.alt = '';
    snapshot.append(previous);
    if (layer) snapshot.append(layer.cloneNode(true));
    picture.append(snapshot);
    const animation = snapshot.animate([{ opacity: 1 }, { opacity: 0 }], { duration: 280, easing: 'ease-out' });
    animation.finished.then(() => snapshot.remove(), () => snapshot.remove());
  }
  function refreshImages() {
    document.querySelectorAll('[data-clock-picture]').forEach(picture => {
      const img = picture.querySelector('img');
      if (!img) return;
      const source = picture.querySelector('source');
      const link = picture.closest('[data-clock-link]');
      const pair = imagePair(picture);
      const dominant = pair.weight >= .5 ? pair.second : pair.first;
      if ('src' in img.dataset) img.dataset.src = dominant;
      if (link) link.href = dominant;
      let state = pictureStates.get(picture);
      if (!state) {
        state = { key: '', layer: null, version: 0, ready: false };
        pictureStates.set(picture, state);
        img.addEventListener('load', refreshImages);
        img.addEventListener('error', () => fallback(picture));
      }
      if (!img.getAttribute('src')) return;
      // Leave lazy gallery cards lazy; blend only once the browser has loaded them.
      const blendable = typeof window.Image === 'function' && (img.loading !== 'lazy' || (img.complete && img.naturalWidth));
      if (picture.dataset.clockExposure === 'single' && blendable && !preference.matches) {
        // Independent hero exposures must not ghost their lettering for hours.
        const nextKey = `single|${dominant}`;
        if (state.key === nextKey) return;
        state.key = nextKey; state.ready = false;
        const version = ++state.version;
        load(dominant).then(ok => {
          if (state.version !== version) return;
          if (!ok && dominant !== picture.dataset.clockDefault) {
            if (!failures.has(picture)) failures.set(picture, new Set());
            failures.get(picture).add(dominant);
            state.key = '';
            refreshImages();
            return;
          }
          if (source.srcset !== dominant) fadePrevious(picture, img, null);
          source.srcset = dominant;
          if (state.layer) state.layer.style.opacity = '0';
          state.ready = true;
        });
        return;
      }
      if (!blendable || pair.first === pair.second || preference.matches) {
        if (source.srcset !== dominant) source.srcset = dominant;
        if (state.layer) state.layer.style.opacity = '0';
        state.ready = false;
        state.key = '';
        state.version++;
        return;
      }
      const nextKey = `${pair.first}|${pair.second}`;
      if (state.key === nextKey && state.ready) {
        state.layer.style.opacity = String(pair.weight);
        return;
      }
      if (state.key === nextKey) return;
      state.key = nextKey; state.ready = false;
      const version = ++state.version;
      Promise.all([load(pair.first), load(pair.second)]).then(([a, b]) => {
        if (state.version !== version) return; // A newer hand position wins a load race.
        if (!a || !b) {
          if (!failures.has(picture)) failures.set(picture, new Set());
          if (!a) failures.get(picture).add(pair.first);
          if (!b) failures.get(picture).add(pair.second);
          state.key = '';
          refreshImages();
          return;
        }
        fadePrevious(picture, img, state.layer);
        if (!state.layer) {
          state.layer = document.createElement('span');
          state.layer.className = 'clock-image-layer';
          state.layer.setAttribute('aria-hidden', 'true');
          const overlay = img.cloneNode(false);
          overlay.removeAttribute('data-src'); overlay.removeAttribute('fetchpriority');
          overlay.alt = ''; overlay.loading = 'eager';
          overlay.style.objectFit = window.getComputedStyle(img).objectFit || 'cover';
          overlay.style.objectPosition = window.getComputedStyle(img).objectPosition || '50% 50%';
          state.layer.append(overlay); picture.append(state.layer);
        }
        state.layer.querySelector('img').src = pair.second;
        source.srcset = pair.first;
        state.ready = true;
        state.layer.style.opacity = String(imagePair(picture).weight);
      });
    });
  }
  function fallback(picture) {
    const pair = imagePair(picture);
    if (pair.first === picture.dataset.clockDefault && pair.second === pair.first) return;
    if (!failures.has(picture)) failures.set(picture, new Set());
    for (const url of [pair.first, pair.second]) if (url !== picture.dataset.clockDefault) failures.get(picture).add(url);
    const img = picture.querySelector('img');
    picture.querySelector('source').srcset = picture.dataset.clockDefault;
    if (img && img.getAttribute('src')) img.src = picture.dataset.clockDefault;
    const state = pictureStates.get(picture);
    if (state) { state.key = ''; state.version++; }
    refreshImages();
  }
  document.addEventListener('error', event => {
    if (event.target.tagName !== 'IMG') return;
    const picture = event.target.closest('[data-clock-picture]');
    if (picture) fallback(picture);
  }, true);

  function render() {
    const minute = wrap(visual);
    palette(minute);
    root.style.setProperty('--clock-hour-angle', `${hourAngle}deg`);
    root.style.setProperty('--clock-minute-angle', `${minuteAngle}deg`);
    refreshImages();
  }
  function sync() {
    const time = format(target);
    const phase = phaseFor(wrap(target));
    root.dataset.dayPhase = phase;
    document.querySelectorAll('[data-clock-label]').forEach(el => { el.textContent = `${fa(time)} · ${labels[phase]}`; });
    document.querySelectorAll('[data-clock-time]').forEach(el => { el.textContent = fa(time); el.dateTime = time; });
    document.querySelectorAll('[data-clock-halfday]').forEach(el => {
      el.textContent = wrap(target) < 720 ? 'قبل از ظهر' : 'بعد از ظهر';
      el.setAttribute('aria-pressed', String(wrap(target) >= 720));
    });
    document.querySelectorAll('[data-clock-open]').forEach(el => el.setAttribute('aria-label', `ساعت سایت ${fa(time)}، ${labels[phase]}؛ ${manual ? 'زمان دستی' : 'زمان واقعی'}؛ تنظیم ساعت`));
    document.querySelectorAll('[data-clock-status]').forEach(el => { el.textContent = `${manual ? 'زمان دلخواه تو' : 'زمان واقعی دستگاه'} · ${labels[phase]}`; });
    document.querySelectorAll('[data-clock-hand]').forEach(hand => {
      hand.setAttribute('aria-valuenow', String(hand.dataset.clockHand === 'hour' ? Math.floor(wrap(target) / 60) : Math.floor(wrap(target) % 60)));
      hand.setAttribute('aria-valuetext', `${fa(time)}، ${labels[phase]}`);
    });
    const input = document.querySelector('[data-clock-input]');
    if (input && document.activeElement !== input) input.value = time;
  }
  function animate(timestamp) {
    frame = null;
    const dt = Math.min(50, lastFrame === null ? 16 : timestamp - lastFrame);
    lastFrame = timestamp;
    const delta = cyclicDelta(target, visual, 1440);
    const hourDelta = cyclicDelta(target / 2, hourAngle, 360);
    const minuteDelta = cyclicDelta(target * 6, minuteAngle, 360);
    const ease = 1 - Math.exp(-dt / (dragging ? 38 : 145));
    visual += delta * ease;
    hourAngle += hourDelta * ease;
    minuteAngle += minuteDelta * ease;
    const settled = Math.abs(delta) < .015 && Math.abs(hourDelta) < .02 && Math.abs(minuteDelta) < .02;
    if (settled) { visual = target; hourAngle += hourDelta; minuteAngle += minuteDelta; }
    painting = true; render(); painting = false;
    if (!settled) frame = window.requestAnimationFrame(animate);
    else lastFrame = null;
  }
  function paint() {
    sync();
    if (preference.matches) {
      if (frame !== null) window.cancelAnimationFrame(frame);
      frame = null; lastFrame = null; visual = target; hourAngle = target / 2; minuteAngle = target * 6; render();
    } else if (frame === null && !painting) frame = window.requestAnimationFrame(animate);
  }
  const save = () => {
    try {
      if (manual) window.sessionStorage.setItem(key, manual);
      else window.sessionStorage.removeItem(key);
    } catch { /* An in-memory choice still works when storage is unavailable. */ }
  };
  const announce = () => document.querySelectorAll('[data-clock-announcement]').forEach(el => { el.textContent = `ساعت سایت ${fa(format(target))}، ${labels[phaseFor(wrap(target))]}`; });
  const setMinutes = (minutes, persist = true) => { target = wrap(minutes); manual = format(target); if (persist) save(); paint(); };
  const setTime = value => { if (valid(value)) { setMinutes(parse(value)); announce(); } };
  const useRealTime = () => { manual = null; target = localMinutes(); save(); paint(); announce(); };
  window.TabloClock = { prepare, refreshImages, setTime, useRealTime };
  sync(); render();

  function bindDial(dial) {
    let drag = null;
    const angleAt = event => {
      const rect = dial.getBoundingClientRect();
      return Math.atan2(event.clientX - rect.x - rect.width / 2, -(event.clientY - rect.y - rect.height / 2)) * 180 / Math.PI;
    };
    dial.addEventListener('pointerdown', event => {
      if (event.button !== 0 || !event.isPrimary) return;
      const hit = event.target.closest('[data-clock-hand]');
      const rect = dial.getBoundingClientRect();
      const distance = Math.hypot(event.clientX - rect.x - rect.width / 2, event.clientY - rect.y - rect.height / 2);
      const hand = hit?.dataset.clockHand || (distance < rect.width * .29 ? 'hour' : 'minute');
      drag = { hand, pointerId: event.pointerId, last: angleAt(event), accumulated: 0, start: target, moved: false };
      dragging = true; root.dataset.clockDragging = 'true';
      dial.setPointerCapture(event.pointerId);
      dial.querySelector(`[data-clock-hand="${hand}"]`).focus({ preventScroll: true });
      event.preventDefault();
    });
    dial.addEventListener('pointermove', event => {
      if (!drag || event.pointerId !== drag.pointerId) return;
      const angle = angleAt(event);
      const delta = ((angle - drag.last + 540) % 360) - 180;
      drag.accumulated += delta; drag.last = angle;
      if (Math.abs(drag.accumulated) > 1) drag.moved = true;
      setMinutes(drag.start + drag.accumulated * (drag.hand === 'hour' ? 2 : 1 / 6), false);
    });
    const end = event => {
      if (!drag || event.pointerId !== drag.pointerId) return;
      if (!drag.moved && event.type === 'pointerup') {
        const angle = (angleAt(event) + 360) % 360;
        const currentAngle = drag.hand === 'hour' ? (target % 720) / 2 : (target % 60) * 6;
        const delta = ((angle - currentAngle + 540) % 360) - 180;
        setMinutes(target + delta * (drag.hand === 'hour' ? 2 : 1 / 6));
      }
      drag = null; dragging = false; delete root.dataset.clockDragging;
      setMinutes(Math.round(target)); announce();
      if (dial.hasPointerCapture(event.pointerId)) dial.releasePointerCapture(event.pointerId);
    };
    for (const event of ['pointerup', 'pointercancel', 'lostpointercapture']) dial.addEventListener(event, end);
    dial.querySelectorAll('[data-clock-hand]').forEach(hand => hand.addEventListener('keydown', event => {
      const step = hand.dataset.clockHand === 'hour' ? 60 : 1;
      let minutes = target;
      if (event.key === 'ArrowUp' || event.key === 'ArrowRight') minutes += step;
      else if (event.key === 'ArrowDown' || event.key === 'ArrowLeft') minutes -= step;
      else if (event.key === 'PageUp') minutes += 60;
      else if (event.key === 'PageDown') minutes -= 60;
      else if (event.key === 'Home') minutes = 0;
      else if (event.key === 'End') minutes = 1439;
      else return;
      event.preventDefault(); setMinutes(minutes); announce();
    }));
  }
  const bind = () => {
    const dialog = document.querySelector('[data-clock-dialog]');
    const input = document.querySelector('[data-clock-input]');
    let opener = null;
    document.querySelectorAll('[data-clock-open]').forEach(button => {
      button.hidden = false;
      button.addEventListener('click', () => {
        if (!dialog || typeof dialog.showModal !== 'function') return;
        opener = button; input.value = format(target); dialog.showModal();
        button.setAttribute('aria-expanded', 'true');
        dialog.querySelector('[data-clock-hand="hour"]').focus();
      });
    });
    dialog?.addEventListener('close', () => { opener?.setAttribute('aria-expanded', 'false'); opener?.focus(); });
    document.querySelector('[data-clock-close]')?.addEventListener('click', () => dialog.close());
    document.querySelector('[data-clock-form]')?.addEventListener('submit', event => { event.preventDefault(); if (input.reportValidity()) setTime(input.value); });
    input?.addEventListener('input', () => { if (input.validity.valid) setTime(input.value); });
    document.querySelector('[data-clock-halfday]')?.addEventListener('click', () => { setMinutes(target + 720); announce(); });
    document.querySelectorAll('[data-clock-step]').forEach(button => button.addEventListener('click', () => { setMinutes(target + Number(button.dataset.clockStep)); announce(); }));
    document.querySelector('[data-clock-real]')?.addEventListener('click', useRealTime);
    document.querySelectorAll('[data-clock-dial]').forEach(bindDial);
    document.addEventListener('htmx:afterSwap', refreshImages);
    paint();
  };
  const updateRealTime = () => { if (!manual) { target = localMinutes(); paint(); } };
  window.setInterval(updateRealTime, 10000);
  window.addEventListener('pageshow', updateRealTime);
  document.addEventListener('visibilitychange', () => { if (!document.hidden) updateRealTime(); });
  preference.addEventListener?.('change', paint);
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', bind);
  else bind();
})();
