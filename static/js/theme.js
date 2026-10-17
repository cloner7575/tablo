/* Runs in <head>: resolve the saved/device theme before the first paint. */
(() => {
  const key = 'tablo-theme';
  const root = document.documentElement;
  const device = window.matchMedia('(prefers-color-scheme: dark)');
  const valid = (value) => value === 'light' || value === 'dark' ? value : null;
  const read = () => {
    try { return valid(window.localStorage.getItem(key)); }
    catch { return null; } // Storage may be disabled; switching still works.
  };
  let choice = read();
  const buttons = () => document.querySelectorAll('[data-theme-toggle]');
  const sync = () => buttons().forEach((button) => {
    const dark = root.dataset.theme === 'dark';
    button.setAttribute('aria-pressed', String(dark));
    button.setAttribute('aria-label', dark ? 'تغییر به حالت روشن' : 'تغییر به حالت تاریک');
    button.setAttribute('title', dark ? 'حالت روشن' : 'حالت تاریک');
  });
  const apply = () => {
    root.dataset.theme = choice || (device.matches ? 'dark' : 'light');
    const meta = document.querySelector('meta[name="theme-color"]');
    if (meta) meta.content = meta.dataset[root.dataset.theme] || meta.content;
    sync();
  };
  apply();
  const bind = () => {
    sync();
    buttons().forEach((button) => button.addEventListener('click', () => {
      choice = root.dataset.theme === 'dark' ? 'light' : 'dark';
      try { window.localStorage.setItem(key, choice); }
      catch { /* Session-only preference when persistent storage is blocked. */ }
      apply();
    }));
  };
  device.addEventListener('change', () => { if (!choice) apply(); });
  window.addEventListener('storage', (event) => {
    if (event.key !== key) return;
    choice = valid(event.newValue);
    apply();
  });
  window.addEventListener('pageshow', () => { choice = read(); apply(); });
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', bind);
  else bind();
})();
