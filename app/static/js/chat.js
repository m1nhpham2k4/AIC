document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("chat-form");
  const input = document.getElementById("chat-input");
  const chatBox = document.getElementById("chat-history");
  const greeting = document.querySelector(".center-greeting");

  if (!form || !input || !chatBox) return; // tránh lỗi nếu chưa có DOM

  form.addEventListener("submit", async (e) => {
    e.preventDefault();

    const message = input.value.trim();
    if (!message) return;

    // Ẩn lời chào nếu có
    greeting?.classList.add("hidden");

    // Hiển thị tin nhắn người dùng
    const userBubble = document.createElement("div");
    userBubble.className = "bubble user";
    userBubble.innerText = message;
    chatBox.appendChild(userBubble);
    scrollToBottom();

    input.value = "";
    input.focus();

    try {
      // Gửi truy vấn đến API mới: /api/search?q=...
      const res = await fetch(`/api/search?q=${encodeURIComponent(message)}&topk=12`);
      const data = await res.json();

      const botBubble = document.createElement("div");
      botBubble.className = "bubble bot";

      if (data.results && data.results.length > 0) {
        let html = `<strong>Kết quả cho "<em>${escapeHTML(data.query || message)}</em>":</strong>`;
        html += `<ul style="padding-left:20px; line-height:1.6;">`;

        data.results.forEach(item => {
          const score = (typeof item.score === "number")
            ? item.score.toFixed(3)
            : item.score ?? "-";

          // nếu backend trả đường dẫn ảnh local -> hiển thị thumbnail
          const thumb = item.image
            ? `/api/preview_image?path=${encodeURIComponent(item.image)}`
            : null;

          html += `<li>
            ${thumb ? `<img src="${thumb}" alt="thumb" style="height:44px;vertical-align:middle;margin-right:8px;border-radius:4px;">` : ""}
            <code>${escapeHTML(item.video || "-")}</code>
            &nbsp;|&nbsp; frame: <b>${item.frame_idx ?? "-"}</b>
            &nbsp;|&nbsp; score: <span style="color:gray;">${score}</span>
          </li>`;
        });

        html += "</ul>";
        botBubble.innerHTML = html;
      } else {
        botBubble.innerText = "❌ Không tìm thấy kết quả nào.";
      }

      chatBox.appendChild(botBubble);
    } catch (err) {
      const errorBubble = document.createElement("div");
      errorBubble.className = "bubble bot";
      errorBubble.innerText = "⚠️ Lỗi khi gọi API tìm kiếm.";
      chatBox.appendChild(errorBubble);
      console.error(err);
    }

    scrollToBottom();
  });

  function scrollToBottom() {
    chatBox.scrollTop = chatBox.scrollHeight;
  }

  function escapeHTML(s) {
    return s.replace(/[&<>"']/g, (m) => ({
      "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#039;"
    }[m]));
  }
});
