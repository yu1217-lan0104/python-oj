/* 轻量交互：复制样例、编辑器体验、草稿自动保存、提交防重复 */
(function () {
  "use strict";

  function flash(text) {
    const tip = document.createElement("div");
    tip.textContent = text;
    tip.style.cssText =
      "position:fixed;left:50%;bottom:36px;transform:translateX(-50%);" +
      "background:#101828;color:#fff;padding:8px 16px;border-radius:999px;" +
      "font-size:13px;z-index:2000;opacity:0;transition:opacity .2s ease;";
    document.body.appendChild(tip);
    requestAnimationFrame(function () {
      tip.style.opacity = "1";
    });
    setTimeout(function () {
      tip.style.opacity = "0";
      setTimeout(function () {
        tip.remove();
      }, 220);
    }, 1400);
  }

  function copyText(text) {
    if (navigator.clipboard && window.isSecureContext) {
      return navigator.clipboard.writeText(text);
    }
    const area = document.createElement("textarea");
    area.value = text;
    area.style.position = "fixed";
    area.style.opacity = "0";
    document.body.appendChild(area);
    area.select();
    try {
      document.execCommand("copy");
    } catch (err) {
      /* 忽略：部分浏览器禁用了 execCommand */
    }
    area.remove();
    return Promise.resolve();
  }

  /* 复制按钮：样例输入/输出、提交的代码 */
  document.addEventListener("click", function (event) {
    const btn = event.target.closest("[data-copy]");
    if (!btn) return;
    const text = btn.getAttribute("data-copy") || "";
    copyText(text).then(function () {
      flash("已复制到剪贴板");
    });
  });

  /* 代码编辑器 */
  const editor = document.getElementById("code");
  if (!editor) {
    return;
  }

  const counter = document.getElementById("code-count");
  const form = document.getElementById("submit-form");
  const submitBtn = document.getElementById("submit-btn");
  const hint = document.getElementById("draft-hint");
  const clearDraftBtn = document.getElementById("clear-draft");
  const problemId = form ? form.dataset.problemId : "";
  const draftKey = problemId ? "pyoj:draft:" + problemId : "";
  const defaultCode = editor.getAttribute("data-default") || "";
  let draftTimer = null;

  function setHint(text) {
    if (hint) hint.textContent = text;
  }

  function updateCount() {
    if (counter) counter.textContent = editor.value.length + " 字符";
  }

  function formatTime(timestamp) {
    const date = new Date(timestamp);
    const pad = function (n) {
      return String(n).padStart(2, "0");
    };
    return date.getMonth() + 1 + "-" + pad(date.getDate()) + " " + pad(date.getHours()) + ":" + pad(date.getMinutes());
  }

  /* ---------- 草稿：存在浏览器 localStorage 里，按题目分开 ---------- */
  function saveDraft() {
    if (!draftKey) return;
    try {
      if (editor.value === defaultCode || !editor.value.trim()) {
        localStorage.removeItem(draftKey);
        setHint("草稿会自动保存在本机浏览器");
        if (clearDraftBtn) clearDraftBtn.hidden = true;
        return;
      }
      const now = Date.now();
      localStorage.setItem(draftKey, JSON.stringify({ code: editor.value, at: now }));
      setHint("草稿已保存 " + formatTime(now));
      if (clearDraftBtn) clearDraftBtn.hidden = false;
    } catch (err) {
      setHint("浏览器禁用了本地存储，草稿无法保存");
    }
  }

  function restoreDraft() {
    if (!draftKey) return;
    let draft = null;
    try {
      const raw = localStorage.getItem(draftKey);
      draft = raw ? JSON.parse(raw) : null;
    } catch (err) {
      draft = null;
    }
    if (draft && draft.code && draft.code !== defaultCode) {
      editor.value = draft.code;
      setHint("已恢复上次草稿（" + formatTime(draft.at) + "）");
      if (clearDraftBtn) clearDraftBtn.hidden = false;
    }
    updateCount();
  }

  restoreDraft();

  editor.addEventListener("input", function () {
    updateCount();
    if (draftTimer) clearTimeout(draftTimer);
    draftTimer = setTimeout(saveDraft, 600);
  });

  if (clearDraftBtn) {
    clearDraftBtn.addEventListener("click", function () {
      if (draftKey) {
        try {
          localStorage.removeItem(draftKey);
        } catch (err) {
          /* 忽略 */
        }
      }
      editor.value = defaultCode;
      updateCount();
      clearDraftBtn.hidden = true;
      setHint("草稿已清空");
    });
  }

  /* Tab 缩进 4 个空格，Shift+Tab 回退缩进 */
  editor.addEventListener("keydown", function (event) {
    if (event.key === "Tab") {
      event.preventDefault();
      const start = editor.selectionStart;
      const end = editor.selectionEnd;
      if (event.shiftKey) {
        const before = editor.value.slice(0, start);
        const lineStart = before.lastIndexOf("\n") + 1;
        const segment = editor.value.slice(lineStart, end);
        const cleaned = segment.replace(/^ {1,4}/, "");
        const removed = segment.length - cleaned.length;
        editor.value = editor.value.slice(0, lineStart) + cleaned + editor.value.slice(end);
        editor.selectionStart = editor.selectionEnd = Math.max(lineStart, start - removed);
      } else {
        editor.value = editor.value.slice(0, start) + "    " + editor.value.slice(end);
        editor.selectionStart = editor.selectionEnd = start + 4;
      }
      updateCount();
    }

    /* Ctrl / Cmd + Enter 提交 */
    if ((event.ctrlKey || event.metaKey) && event.key === "Enter" && form) {
      event.preventDefault();
      form.requestSubmit ? form.requestSubmit() : form.submit();
    }
  });

  /* 防止重复提交 */
  if (form) {
    form.addEventListener("submit", function () {
      if (!editor.value.trim()) {
        return;
      }
      saveDraft();
      if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.textContent = "正在判题…";
      }
    });
    window.addEventListener("pageshow", function () {
      if (submitBtn) {
        submitBtn.disabled = false;
        submitBtn.textContent = "提交判题";
      }
    });
  }
})();
