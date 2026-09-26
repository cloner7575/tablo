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

function initMultiImagePreview() {
  const input = document.querySelector("[data-multi-preview]");
  const box = document.querySelector("[data-image-preview]");
  const list = document.querySelector("[data-image-preview-list]");
  if (!input || !box || !list) {
    return;
  }

  input.addEventListener("change", () => {
    list.replaceChildren();
    const files = Array.from(input.files || []).slice(0, 6);
    if (!files.length) {
      box.hidden = true;
      return;
    }
    box.hidden = false;
    files.forEach((file) => {
      if (!file.type.startsWith("image/")) {
        return;
      }
      const li = document.createElement("li");
      const img = document.createElement("img");
      img.alt = file.name;
      img.src = URL.createObjectURL(file);
      img.onload = () => URL.revokeObjectURL(img.src);
      li.appendChild(img);
      list.appendChild(li);
    });
  });
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", initMultiImagePreview);
} else {
  initMultiImagePreview();
}
