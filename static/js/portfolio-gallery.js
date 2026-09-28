// Portfolio gallery: main stage + thumbnail row, and a lightbox with a
// thumbnail grid. Without JS the stage is a scroll-snap strip, thumbnails are
// anchors into it and every tile links to its file, so nothing is gated on JS.

(() => {
  const gallery = document.querySelector("[data-gallery]");
  if (!gallery) {
    return;
  }

  const isRtl = document.documentElement.dir === "rtl";
  const faDigits = new Intl.NumberFormat("fa-IR", { useGrouping: false });
  const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)");
  const SWIPE_MIN_PX = 40;

  // --- Stage and thumbnail row ------------------------------------------

  const track = gallery.querySelector("[data-gallery-track]");
  const stageSlides = Array.from(gallery.querySelectorAll("[data-gallery-slide]"));
  const stageThumbs = Array.from(gallery.querySelectorAll("[data-gallery-thumb]"));
  const moreThumb = gallery.querySelector("[data-gallery-more]");
  const dots = Array.from(gallery.querySelectorAll(".pf-gallery__dots li"));
  const zoom = gallery.querySelector("[data-gallery-zoom]");
  let stageIndex = 0;

  function markStage(index) {
    stageIndex = index;
    stageThumbs.forEach((thumb) => {
      if (Number(thumb.dataset.galleryThumb) === index) {
        thumb.setAttribute("aria-current", "true");
      } else {
        thumb.removeAttribute("aria-current");
      }
    });
    if (moreThumb) {
      moreThumb.classList.toggle("is-current", index >= stageThumbs.length);
    }
    dots.forEach((dot, i) => dot.classList.toggle("is-active", i === index));
  }

  function scrollStageTo(index) {
    const slide = stageSlides[index];
    if (!slide || !track) {
      return;
    }
    // Horizontal offsets are negative in RTL scroll containers.
    const direction = isRtl ? -1 : 1;
    track.scrollTo({
      left: direction * index * track.clientWidth,
      behavior: reduceMotion.matches ? "auto" : "smooth",
    });
    markStage(index);
  }

  stageThumbs.forEach((thumb) => {
    thumb.addEventListener("click", (event) => {
      event.preventDefault();
      scrollStageTo(Number(thumb.dataset.galleryThumb) || 0);
    });
  });

  if (track) {
    let ticking = false;
    track.addEventListener(
      "scroll",
      () => {
        if (ticking) {
          return;
        }
        ticking = true;
        requestAnimationFrame(() => {
          ticking = false;
          const width = track.clientWidth || 1;
          const index = Math.round(Math.abs(track.scrollLeft) / width);
          if (index !== stageIndex && index < stageSlides.length) {
            markStage(index);
          }
        });
      },
      { passive: true },
    );
    // Keep the current slide aligned when the stage width changes.
    new ResizeObserver(() => {
      const direction = isRtl ? -1 : 1;
      track.scrollTo({ left: direction * stageIndex * track.clientWidth });
    }).observe(track);
  }

  // --- Lightbox ---------------------------------------------------------

  const dialog = document.querySelector("[data-lightbox]");
  if (!dialog || typeof dialog.showModal !== "function") {
    return;
  }

  const slides = Array.from(dialog.querySelectorAll("[data-slide]"));
  const thumbs = Array.from(dialog.querySelectorAll("[data-lightbox-go]"));
  const filters = Array.from(dialog.querySelectorAll("[data-lightbox-filter]"));
  const indexLabel = dialog.querySelector("[data-lightbox-index]");
  const totalLabel = dialog.querySelector("[data-lightbox-total]");
  const stage = dialog.querySelector("[data-lightbox-stage]");
  let visible = slides.map((_, i) => i);
  let current = 0;
  let opener = null;

  function loadMedia(slide) {
    const lazy = slide?.querySelector("img[data-src]");
    if (lazy && !lazy.getAttribute("src")) {
      lazy.src = lazy.dataset.src;
    }
  }

  function deactivate(slide) {
    const video = slide.querySelector("video");
    if (video && !video.paused) {
      video.pause();
    }
    // Unloading the iframe is the only reliable way to stop an Aparat embed.
    const frame = slide.querySelector("iframe[data-src]");
    if (frame && frame.getAttribute("src")) {
      frame.removeAttribute("src");
    }
    slide.hidden = true;
  }

  function activate(slide) {
    slide.hidden = false;
    loadMedia(slide);
    const video = slide.querySelector("video");
    if (video && video.preload === "none") {
      video.preload = "metadata";
    }
    const frame = slide.querySelector("iframe[data-src]");
    if (frame && !frame.getAttribute("src")) {
      frame.src = frame.dataset.src;
    }
  }

  function show(index) {
    current = index;
    slides.forEach((slide, i) => {
      if (i !== index && !slide.hidden) {
        deactivate(slide);
      }
    });
    activate(slides[index]);
    const position = visible.indexOf(index);
    const count = visible.length;
    loadMedia(slides[visible[(position + 1) % count]]);
    loadMedia(slides[visible[(position - 1 + count) % count]]);
    if (indexLabel) {
      indexLabel.textContent = faDigits.format(position + 1);
    }
    thumbs.forEach((thumb) => {
      if (Number(thumb.dataset.lightboxGo) === index) {
        thumb.setAttribute("aria-current", "true");
        thumb.scrollIntoView({ block: "nearest", inline: "nearest" });
      } else {
        thumb.removeAttribute("aria-current");
      }
    });
  }

  function step(delta) {
    const count = visible.length;
    if (count < 2) {
      return;
    }
    const position = visible.indexOf(current);
    show(visible[(position + delta + count) % count]);
  }

  function applyFilter(kind) {
    visible = slides
      .map((slide, i) => (kind === "all" || slide.dataset.kind === kind ? i : -1))
      .filter((i) => i >= 0);
    filters.forEach((button) => {
      button.setAttribute("aria-pressed", String(button.dataset.lightboxFilter === kind));
    });
    thumbs.forEach((thumb) => {
      thumb.parentElement.hidden = !visible.includes(Number(thumb.dataset.lightboxGo));
    });
    if (totalLabel) {
      totalLabel.textContent = faDigits.format(visible.length);
    }
    dialog.classList.toggle("is-single", visible.length < 2);
    show(visible.includes(current) ? current : visible[0]);
  }

  function open(index, trigger) {
    opener = trigger || null;
    dialog.showModal();
    document.body.classList.add("lightbox-open");
    if (filters.length) {
      applyFilter("all");
    }
    show(index);
  }

  gallery.querySelectorAll("[data-gallery-open]").forEach((trigger) => {
    trigger.addEventListener("click", (event) => {
      event.preventDefault();
      open(Number(trigger.dataset.galleryOpen) || 0, trigger);
    });
  });

  if (zoom) {
    zoom.hidden = false;
    zoom.addEventListener("click", () => open(stageIndex, zoom));
  }

  dialog.addEventListener("close", () => {
    slides.forEach((slide) => {
      if (!slide.hidden) {
        deactivate(slide);
      }
    });
    document.body.classList.remove("lightbox-open");
    // Leave the page on whatever the visitor last looked at.
    if (current < stageSlides.length && current !== stageIndex) {
      scrollStageTo(current);
    }
    opener?.focus({ preventScroll: true });
  });

  dialog.querySelector("[data-lightbox-close]")?.addEventListener("click", () => dialog.close());
  dialog.querySelector("[data-lightbox-prev]")?.addEventListener("click", () => step(-1));
  dialog.querySelector("[data-lightbox-next]")?.addEventListener("click", () => step(1));
  thumbs.forEach((thumb) => {
    thumb.addEventListener("click", () => show(Number(thumb.dataset.lightboxGo) || 0));
  });
  filters.forEach((button) => {
    button.addEventListener("click", () => applyFilter(button.dataset.lightboxFilter));
  });

  // Clicking the dimmed backdrop (the dialog element itself) closes it.
  dialog.addEventListener("click", (event) => {
    if (event.target === dialog) {
      dialog.close();
    }
  });

  dialog.addEventListener("keydown", (event) => {
    if (event.key === "Escape") {
      event.preventDefault();
      dialog.close();
      return;
    }
    if (event.target instanceof HTMLVideoElement) {
      return;
    }
    const forwardKey = isRtl ? "ArrowLeft" : "ArrowRight";
    const backKey = isRtl ? "ArrowRight" : "ArrowLeft";
    if (event.key === forwardKey) {
      event.preventDefault();
      step(1);
    } else if (event.key === backKey) {
      event.preventDefault();
      step(-1);
    }
  });

  let startX = null;
  let startY = null;
  stage.addEventListener("pointerdown", (event) => {
    if (event.pointerType === "mouse") {
      return;
    }
    startX = event.clientX;
    startY = event.clientY;
  });
  stage.addEventListener("pointerup", (event) => {
    if (startX === null) {
      return;
    }
    const dx = event.clientX - startX;
    const dy = event.clientY - startY;
    startX = null;
    if (Math.abs(dx) < SWIPE_MIN_PX || Math.abs(dx) < Math.abs(dy)) {
      return;
    }
    // In RTL the next item sits to the left, so dragging right reveals it.
    const forward = isRtl ? dx > 0 : dx < 0;
    step(forward ? 1 : -1);
  });
  stage.addEventListener("pointercancel", () => {
    startX = null;
  });
})();
