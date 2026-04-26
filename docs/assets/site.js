const copyButtons = document.querySelectorAll('.copy-button');

for (const button of copyButtons) {
  button.addEventListener('click', async () => {
    const text = button.getAttribute('data-copy');
    if (!text) {
      return;
    }

    try {
      await navigator.clipboard.writeText(text);
      const original = button.textContent;
      button.textContent = 'Copied';
      button.classList.add('is-copied');
      window.setTimeout(() => {
        button.textContent = original;
        button.classList.remove('is-copied');
      }, 1400);
    } catch {
      button.textContent = 'Copy failed';
      window.setTimeout(() => {
        button.textContent = 'Copy';
      }, 1400);
    }
  });
}
