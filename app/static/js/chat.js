document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("chat-form");
  const input = document.getElementById("chat-input");
  const chatBox = document.getElementById("chat-history");
  const greeting = document.querySelector(".center-greeting");

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
      // Gửi truy vấn đến API /search
      const res = await fetch(`/search?query=${encodeURIComponent(message)}`);
      const data = await res.json();

      const botBubble = document.createElement("div");
      botBubble.className = "bubble bot";

      if (data.results && data.results.length > 0) {
        let html = `<strong>Kết quả cho "<em>${data.query}</em>":</strong><ul style="padding-left:20px;">`;
        data.results.forEach(item => {
          html += `<li>${item.path} <span style="color:gray;">(score: ${item.score})</span></li>`;
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
});
