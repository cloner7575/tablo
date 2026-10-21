(() => {
  const button = document.querySelector('[data-mcp-copy]');
  const address = document.querySelector('#mcp-address');
  const status = document.querySelector('[data-copy-status]');
  button?.addEventListener('click', async () => {
    try {
      await navigator.clipboard.writeText(address.value);
      status.textContent = 'آدرس اتصال کپی شد.';
    } catch {
      address.focus();
      address.select();
      status.textContent = 'آدرس انتخاب شد؛ آن را کپی کنید.';
    }
  });
})();
