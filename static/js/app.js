document.documentElement.dataset.js = "true";

// HTMX drops non-2xx responses by default. Our views answer 400 for invalid
// forms and 503 for degraded dependencies and still render a partial, so swap
// those instead of leaving the user staring at an unchanged page.
const SWAPPABLE_ERROR_STATUSES = [400, 422, 503];

document.addEventListener("htmx:beforeSwap", (event) => {
  if (SWAPPABLE_ERROR_STATUSES.includes(event.detail.xhr.status)) {
    event.detail.shouldSwap = true;
    event.detail.isError = false;
  }
});

function closeMobileNav() {
  const toggle = document.querySelector("[data-nav-toggle]");
  const drawer = document.querySelector("[data-nav-drawer]");
  if (!toggle || !drawer) {
    return;
  }
  toggle.setAttribute("aria-expanded", "false");
  drawer.hidden = true;
  document.body.classList.remove("nav-open");
}

function openMobileNav() {
  const toggle = document.querySelector("[data-nav-toggle]");
  const drawer = document.querySelector("[data-nav-drawer]");
  if (!toggle || !drawer) {
    return;
  }
  toggle.setAttribute("aria-expanded", "true");
  drawer.hidden = false;
  document.body.classList.add("nav-open");
}

function initMobileNav() {
  const toggle = document.querySelector("[data-nav-toggle]");
  const drawer = document.querySelector("[data-nav-drawer]");
  if (!toggle || !drawer) {
    return;
  }

  toggle.addEventListener("click", (event) => {
    event.preventDefault();
    if (toggle.getAttribute("aria-expanded") === "true") {
      closeMobileNav();
    } else {
      openMobileNav();
    }
  });

  drawer.addEventListener("click", (event) => {
    if (event.target.closest("a, button")) {
      closeMobileNav();
    }
  });
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", initMobileNav);
} else {
  initMobileNav();
}

document.addEventListener("keydown", (event) => {
  if (event.key === "Escape") {
    closeMobileNav();
  }
});

const PREVIEW_LIMIT = 12;

function previewItem(file) {
  const li = document.createElement("li");
  const url = URL.createObjectURL(file);
  if (file.type.startsWith("image/")) {
    const img = document.createElement("img");
    img.alt = file.name;
    img.src = url;
    img.onload = () => URL.revokeObjectURL(url);
    li.appendChild(img);
    return li;
  }
  if (file.type.startsWith("video/")) {
    li.classList.add("is-video");
    const video = document.createElement("video");
    video.src = url;
    video.muted = true;
    video.playsInline = true;
    video.preload = "metadata";
    video.setAttribute("aria-label", file.name);
    li.appendChild(video);
    return li;
  }
  return null;
}

function initMultiImagePreview() {
  document.querySelectorAll("[data-multi-preview]").forEach((input) => {
    const scope = input.closest("[data-preview-scope]") || input.closest("form") || document;
    const box = scope.querySelector("[data-image-preview]");
    const list = scope.querySelector("[data-image-preview-list]");
    if (!box || !list) {
      return;
    }
    input.addEventListener("change", () => {
      list.replaceChildren();
      const files = Array.from(input.files || []).slice(0, PREVIEW_LIMIT);
      const items = files.map(previewItem).filter(Boolean);
      box.hidden = items.length === 0;
      items.forEach((li) => list.appendChild(li));
    });
  });
}

// Plain multipart POSTs can take a while on slow links: block double submits
// and tell the user the upload is running.
function initBusySubmit() {
  document.querySelectorAll("form[data-busy-submit]").forEach((form) => {
    form.addEventListener("submit", () => {
      const button = form.querySelector("[type=submit][data-busy-label]");
      form.setAttribute("aria-busy", "true");
      if (!button) {
        return;
      }
      // Defer so the submitter's own name/value still reaches the server.
      window.setTimeout(() => {
        button.disabled = true;
        button.textContent = button.dataset.busyLabel;
      }, 0);
    });
  });
}

function initConfirmForms() {
  document.querySelectorAll("form[data-confirm]").forEach((form) => {
    form.addEventListener("submit", (event) => {
      if (!window.confirm(form.dataset.confirm)) {
        event.preventDefault();
        event.stopImmediatePropagation();
      }
    });
  });
}

function initTabs() {
  document.querySelectorAll("[data-tabs]").forEach((tablist) => {
    const tabs = Array.from(tablist.querySelectorAll("[role=tab]"));
    const panels = tabs.map((tab) => document.getElementById(tab.getAttribute("aria-controls")));
    const select = (index, focus) => {
      tabs.forEach((tab, i) => {
        const active = i === index;
        tab.setAttribute("aria-selected", String(active));
        tab.tabIndex = active ? 0 : -1;
        if (panels[i]) {
          panels[i].hidden = !active;
        }
      });
      if (focus) {
        tabs[index].focus();
      }
    };
    const initial = Math.max(
      tabs.findIndex((tab) => tab.getAttribute("aria-selected") === "true"),
      0,
    );
    tablist.hidden = false;
    select(initial, false);

    const isRtl = document.documentElement.dir === "rtl";
    tabs.forEach((tab, i) => {
      tab.addEventListener("click", () => select(i, false));
      tab.addEventListener("keydown", (event) => {
        const forward = isRtl ? "ArrowLeft" : "ArrowRight";
        const back = isRtl ? "ArrowRight" : "ArrowLeft";
        let next = null;
        if (event.key === forward) next = (i + 1) % tabs.length;
        if (event.key === back) next = (i - 1 + tabs.length) % tabs.length;
        if (event.key === "Home") next = 0;
        if (event.key === "End") next = tabs.length - 1;
        if (next !== null) {
          event.preventDefault();
          select(next, true);
        }
      });
    });
  });
}

// The input itself covers the zone, so this only mirrors state for styling
// and names the chosen files; drop and click stay native.
function initDropZones() {
  const faNumber = new Intl.NumberFormat("fa-IR");
  document.querySelectorAll("[data-drop]").forEach((zone) => {
    const input = zone.querySelector("input[type=file]");
    const label = zone.querySelector("[data-drop-files]");
    if (!input) {
      return;
    }
    const setDragging = (on) => zone.classList.toggle("is-dragging", on);
    input.addEventListener("dragenter", () => setDragging(true));
    input.addEventListener("dragleave", () => setDragging(false));
    input.addEventListener("drop", () => setDragging(false));
    input.addEventListener("change", () => {
      const files = Array.from(input.files || []);
      zone.classList.toggle("has-files", files.length > 0);
      if (!label) {
        return;
      }
      if (files.length === 0) {
        label.textContent = "";
      } else if (files.length === 1) {
        label.textContent = files[0].name;
      } else {
        label.textContent = `${faNumber.format(files.length)} فایل انتخاب شد`;
      }
    });
  });
}

function initForms() {
  initConfirmForms();
  initBusySubmit();
  initDropZones();
  initMultiImagePreview();
  initTabs();
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", initForms);
} else {
  initForms();
}
