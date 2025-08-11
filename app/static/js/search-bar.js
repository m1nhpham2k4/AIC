// static/js/search-bar.js
document.addEventListener("DOMContentLoaded", () => {
  const input   = document.getElementById("search-input");
  const button  = document.getElementById("search-btn");
  const preview = document.getElementById("preview");

  if (!input || !button || !preview) return;

  // bấm nút -> tìm 100 ảnh
  button.addEventListener("click", () => {
    const q = input.value.trim();
    if (q) doSearch(q, 100);
  });

  // nhấn Enter -> tìm 100 ảnh
  let composing = false;                // xử lý gõ tiếng Việt/IME
  input.addEventListener("compositionstart", () => composing = true);
  input.addEventListener("compositionend",   () => composing = false);
  input.addEventListener("keydown", (e) => {
    if (composing) return;
    if (e.key === "Enter" || e.keyCode === 13) {
      e.preventDefault();
      const q = input.value.trim();
      if (q) doSearch(q, 100);
    }
  });

  async function doSearch(q, topk = 100) {
    preview.innerHTML = `<p>🔎 Đang tìm <b>${escapeHTML(q)}</b> (top ${topk})...</p>`;
    try {
      const res = await fetch(`/api/search?q=${encodeURIComponent(q)}&topk=${topk}`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      const results = Array.isArray(data.results) ? data.results : [];

      if (!results.length) {
        preview.innerHTML = `<p>❌ Không thấy kết quả cho "<b>${escapeHTML(q)}</b>".</p>`;
        return;
      }

      // render 100 ảnh (append theo lô để đỡ giật)
      preview.innerHTML = "";
      const chunkSize = 20;
      for (let i = 0; i < results.length; i += chunkSize) {
        const frag = document.createDocumentFragment();
        results.slice(i, i + chunkSize).forEach((item) => {
          const card = document.createElement("div");
          card.className = "preview-card";
          const thumb = item.image
            ? `/api/preview_image?path=${encodeURIComponent(item.image)}`
            : "/static/images/placeholder.png";
          card.innerHTML = `
            <div class="thumb"><img src="${thumb}" alt="thumb"></div>
            <div class="meta">
              <div class="video">${escapeHTML(item.video || "-")}</div>
              <div class="score">score: ${fmt(item.score)}</div>
              <div class="frame">frame: ${item.frame_idx ?? "-"}</div>
            </div>
          `;
          frag.appendChild(card);
        });
        preview.appendChild(frag);
        // nhường UI một nhịp để mượt
        // eslint-disable-next-line no-await-in-loop
        await new Promise(r => setTimeout(r, 0));
      }
    } catch (err) {
      console.error(err);
      preview.innerHTML = `<p style="color:#c00;">⚠️ Lỗi khi gọi /api/search.</p>`;
    }
  }

  function escapeHTML(s) {
    return s.replace(/[&<>"']/g, (m) => ({
      "&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#039;"
    }[m]));
  }
  function fmt(x) {
    const n = Number(x);
    return Number.isFinite(n) ? n.toFixed(3) : "-";
  }
});
