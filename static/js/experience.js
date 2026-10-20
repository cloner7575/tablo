/* Native, progressive motion. Content stays readable if JS or an API is absent. */
(() => {
  const compact = window.matchMedia("(max-width: 767px)");
  const preference = window.matchMedia("(prefers-reduced-motion: reduce)");
  let observed = new WeakSet();
  const revealed = new WeakSet();
  const running = new Set();
  let observer = null;
  let syncAmbient = () => {};
  let observeAmbient = () => {};
  const revealSelector = [
    ".lp-copy > *", ".lp-stage", ".lp-section-head", ".lp-collection", ".lp-steps li", ".lp-final__surface > div", ".lp-final__visual",
    ".at-hero__copy > *", ".at-art__image", ".jd-hero-art", ".at-tool", ".at-section-head", ".gd-gallery-head", ".gd-business-card",
    ".at-project", ".at-maker", ".mp-service-card", ".mp-journey li", ".so-journey li", ".mp-page-head", ".at-reviews blockquote", ".at-workshop__image",
    ".ed-gallery-hero__copy > *", ".ed-gallery-hero__visual", ".ed-idea-card",
    ".ed-article-card", ".ed-featured-article", ".ed-article-head > *",
    ".at-page-head", ".vn-list__hero", ".vn-card", ".svc-hero__copy",
    ".svc-hero__visual", ".vp-header", ".vp-welcome", ".vp-card", ".vp-lead",
    ".req-list__item", ".req-hero", ".ws-welcome", ".ws-project-card", ".ws-board-card", ".auth-card", ".chat-inbox__row", ".error-page",
    ".wz-panel__head", ".chat-room__head", ".vn-hero__content > *", ".pf-summary__title",
  ].join(",");

  function reveal(element) {
    if (preference.matches || revealed.has(element) || typeof element.animate !== "function") return;
    revealed.add(element);
    const photograph = element.matches?.('.lp-stage, .lp-collection, .lp-final__visual');
    const frames = photograph
      ? [{ opacity: .6, translate: '0 26px', scale: '.965' }, { opacity: 1, translate: '0 0', scale: '1' }]
      : [{ opacity: .72, translate: '0 18px' }, { opacity: 1, translate: '0 0' }];
    const animation = element.animate(
      frames,
      { duration: compact.matches ? 480 : photograph ? 850 : 620, delay: Number(element.dataset.revealDelay || 0), easing: "cubic-bezier(.16,1,.3,1)", fill: "backwards" },
    );
    running.add(animation);
    const release = () => running.delete(animation);
    animation.addEventListener("finish", release, { once: true });
    animation.addEventListener("cancel", release, { once: true });
  }

  function initReveals(root = document) {
    document.documentElement.dataset.motion = preference.matches ? "reduced" : "full";
    if (preference.matches || typeof window.IntersectionObserver !== "function") return;
    if (!observer) {
      observer = new IntersectionObserver((entries) => {
        if (preference.matches || !observer) return;
        entries.forEach((entry) => {
          if (!entry.isIntersecting) return;
          observer.unobserve(entry.target);
          reveal(entry.target);
        });
      }, { threshold: 0.08 });
    }
    root.querySelectorAll(revealSelector).forEach((element, index) => {
      if (observed.has(element)) return;
      observed.add(element);
      element.dataset.revealDelay = String(Math.min((index % 4) * 45, 135));
      observer.observe(element);
    });
  }

  function initNavigation() {
    const path = window.location.pathname;
    document.querySelectorAll("[data-navigation]").forEach((group) => {
      let active = null;
      let length = -1;
      group.querySelectorAll("a[href]").forEach((link) => {
        const destination = new URL(link.href, window.location.href).pathname;
        const matches = destination === "/" ? path === "/" : path.startsWith(destination);
        link.removeAttribute("aria-current");
        if (matches && destination.length > length) {
          active = link;
          length = destination.length;
        }
      });
      const account = group.querySelector("[data-account-nav]");
      if (account && (document.body.classList.contains("page-request") || document.body.classList.contains("page-chat"))) active = account;
      active?.setAttribute("aria-current", "page");
    });
  }

  function initFilters() {
    const mobile = window.matchMedia("(max-width: 767px)");
    document.querySelectorAll("[data-responsive-filter]").forEach((panel) => {
      const adapt = () => { panel.open = !mobile.matches || panel.hasAttribute("data-filter-active"); };
      adapt();
      mobile.addEventListener("change", adapt);
    });
  }

  function initReadingProgress() {
    const progress = document.querySelector("[data-reading-progress] span");
    const body = document.querySelector(".ed-article-body");
    if (!progress || !body) return;
    let queued = false;
    const update = () => {
      queued = false;
      const rect = body.getBoundingClientRect();
      const header = document.querySelector(".site-header")?.getBoundingClientRect().height || 0;
      const distance = Math.max(1, rect.height - window.innerHeight + header);
      const amount = Math.max(0, Math.min(1, (header - rect.top) / distance));
      progress.style.transform = `scaleX(${amount})`;
    };
    const schedule = () => {
      if (queued) return;
      queued = true;
      window.requestAnimationFrame(update);
    };
    window.addEventListener("scroll", schedule, { passive: true });
    window.addEventListener("resize", schedule);
    update();
  }

  function initAmbient() {
    const scene = document.querySelector("[data-ambient-motion]");
    if (!scene) return;
    let visible = false;
    let ambientObserver = null;
    syncAmbient = () => {
      scene.dataset.ambient = visible && !preference.matches && !document.hidden ? "running" : "paused";
    };
    observeAmbient = () => {
      if (preference.matches || ambientObserver || typeof window.IntersectionObserver !== "function") return;
      ambientObserver = new IntersectionObserver((entries) => {
        visible = entries[0].isIntersecting;
        syncAmbient();
      }, { threshold: 0.15 });
      ambientObserver.observe(scene);
    };
    document.addEventListener("visibilitychange", syncAmbient);
    observeAmbient();
    syncAmbient();
  }

  function init() {
    initNavigation();
    initFilters();
    initReveals();
    initReadingProgress();
    initAmbient();
    // Server-rendered validation keeps the user at the field that needs attention.
    document.querySelector("main [aria-invalid=true]")?.focus();
  }

  preference.addEventListener("change", () => {
    if (preference.matches) {
      observer?.disconnect();
      observer = null;
      observed = new WeakSet();
      running.forEach((animation) => animation.cancel());
      running.clear();
      document.documentElement.dataset.motion = "reduced";
    } else {
      initReveals();
    }
    observeAmbient();
    syncAmbient();
  });
  document.addEventListener("htmx:afterSwap", (event) => initReveals(event.detail.target));
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
  else init();
})();
