(() => {
  const root = document.querySelector("[data-chat-thread]");
  if (!root) {
    return;
  }

  const messagesEl = root.querySelector("[data-chat-messages]");
  const statusEl = root.querySelector("[data-chat-status]");
  const composer = root.querySelector("[data-chat-composer]");
  const input = root.querySelector("[data-chat-input]");
  const fileInput = root.querySelector("[data-chat-file]");
  const uploadForm = root.querySelector("[data-chat-upload-form]");
  const uploadFile = root.querySelector("[data-chat-upload-file]");
  const uploadBody = root.querySelector("[data-chat-upload-body]");
  const emptyEl = root.querySelector("[data-chat-empty]");
  const userId = Number(root.dataset.userId);
  const canSend = root.dataset.canSend === "1";
  const wsPath = root.dataset.wsPath;

  let socket = null;
  let attempt = 0;
  let closedByServer = false;

  function setStatus(text) {
    if (statusEl) {
      statusEl.textContent = text;
    }
  }

  function scrollToBottom() {
    if (!messagesEl) {
      return;
    }
    messagesEl.scrollTop = messagesEl.scrollHeight;
  }

  function removeEmpty() {
    if (emptyEl) {
      emptyEl.remove();
    }
  }

  function appendMessage(message) {
    if (!messagesEl || !message || !message.id) {
      return;
    }
    if (messagesEl.querySelector(`[data-message-id="${message.id}"]`)) {
      return;
    }
    removeEmpty();
    const mine = Number(message.sender_id) === userId;
    const article = document.createElement("article");
    article.className = `chat-msg ${mine ? "chat-msg--mine" : "chat-msg--theirs"}`;
    article.dataset.messageId = String(message.id);

    const bubble = document.createElement("div");
    bubble.className = "chat-msg__bubble";

    if (message.image_url) {
      const link = document.createElement("a");
      link.className = "chat-msg__image";
      link.href = message.image_url;
      link.target = "_blank";
      link.rel = "noopener";
      const img = document.createElement("img");
      img.src = message.image_url;
      img.alt = "تصویر پیوست";
      img.loading = "lazy";
      link.appendChild(img);
      bubble.appendChild(link);
    }

    if (message.body) {
      const p = document.createElement("p");
      p.className = "chat-msg__body";
      p.textContent = message.body;
      bubble.appendChild(p);
    }

    const time = document.createElement("time");
    time.className = "chat-msg__time";
    if (message.created_at) {
      time.dateTime = message.created_at;
      const d = new Date(message.created_at);
      time.textContent = d.toLocaleTimeString("fa-IR", {
        hour: "2-digit",
        minute: "2-digit",
      });
    }
    bubble.appendChild(time);
    article.appendChild(bubble);
    messagesEl.appendChild(article);
    scrollToBottom();
  }

  function disableComposer(reason) {
    closedByServer = true;
    if (composer) {
      composer.querySelectorAll("input, button").forEach((el) => {
        el.disabled = true;
      });
    }
    setStatus(reason || "گفتگو بسته شد");
  }

  function handlePayload(payload) {
    if (!payload || !payload.type) {
      return;
    }
    if (payload.type === "message.new") {
      appendMessage(payload.message);
      if (socket && socket.readyState === WebSocket.OPEN) {
        socket.send(JSON.stringify({ type: "message.read" }));
      }
      return;
    }
    if (payload.type === "conversation.closed") {
      disableComposer("این گفتگو بسته شد");
      return;
    }
    if (payload.type === "conversation.ready") {
      if (payload.status === "closed") {
        disableComposer("این گفتگو بسته است");
      } else {
        setStatus("متصل");
      }
      return;
    }
    if (payload.type === "error") {
      setStatus(payload.message || "خطا");
      if (payload.code === "closed") {
        disableComposer(payload.message);
      }
    }
  }

  function connect() {
    if (!wsPath || closedByServer) {
      return;
    }
    const proto = window.location.protocol === "https:" ? "wss:" : "ws:";
    const url = `${proto}//${window.location.host}${wsPath}`;
    setStatus(attempt ? "در حال اتصال مجدد…" : "در حال اتصال…");
    socket = new WebSocket(url);

    socket.addEventListener("open", () => {
      attempt = 0;
      setStatus("متصل");
      socket.send(JSON.stringify({ type: "message.read" }));
    });

    socket.addEventListener("message", (event) => {
      try {
        handlePayload(JSON.parse(event.data));
      } catch (_err) {
        setStatus("پیام نامعتبر از سرور");
      }
    });

    socket.addEventListener("close", () => {
      if (closedByServer) {
        return;
      }
      attempt += 1;
      const delay = Math.min(10000, 500 * 2 ** Math.min(attempt, 4));
      setStatus("قطع شد — تلاش مجدد…");
      window.setTimeout(connect, delay);
    });
  }

  if (composer && canSend && input) {
    composer.addEventListener("submit", (event) => {
      event.preventDefault();
      const body = input.value.trim();
      if (!body) {
        return;
      }
      if (!socket || socket.readyState !== WebSocket.OPEN) {
        composer.submit();
        return;
      }
      socket.send(JSON.stringify({ type: "message.send", body }));
      input.value = "";
      input.focus();
    });
  }

  if (fileInput && uploadForm && uploadFile && canSend) {
    fileInput.addEventListener("change", () => {
      if (!fileInput.files || !fileInput.files[0]) {
        return;
      }
      uploadFile.files = fileInput.files;
      if (uploadBody && input) {
        uploadBody.value = input.value.trim();
      }
      uploadForm.submit();
    });
  }

  scrollToBottom();
  connect();
})();
