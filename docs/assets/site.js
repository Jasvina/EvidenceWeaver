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

const revealElements = document.querySelectorAll('[data-reveal]');

if ('IntersectionObserver' in window) {
  const observer = new IntersectionObserver(
    (entries) => {
      for (const entry of entries) {
        if (entry.isIntersecting) {
          entry.target.classList.add('is-visible');
          observer.unobserve(entry.target);
        }
      }
    },
    {
      threshold: 0.18,
      rootMargin: '0px 0px -40px 0px',
    },
  );

  for (const element of revealElements) {
    observer.observe(element);
  }
} else {
  for (const element of revealElements) {
    element.classList.add('is-visible');
  }
}
