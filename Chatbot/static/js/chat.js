document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("chat-form");
  const input = document.getElementById("chat-input");
  const chatBox = document.getElementById("chat-history");
  const greeting = document.querySelector(".center-greeting");

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const message = input.value.trim();
    if (!message) return;

    // Ẩn greeting sau lần gửi đầu tiên
    if (greeting && !greeting.classList.contains("hidden")) {
      greeting.classList.add("hidden");
    }

    // Hiển thị tin nhắn người dùng
    const userBubble = document.createElement("div");
    userBubble.className = "bubble user";
    userBubble.innerText = message;
    chatBox.appendChild(userBubble);

    try {
      const res = await fetch("/chat", {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: new URLSearchParams({ message }),
      });

      const data = await res.json();

      const botBubble = document.createElement("div");
      botBubble.className = "bubble bot";
      botBubble.innerText = data.reply;
      chatBox.appendChild(botBubble);
    } catch (err) {
      const errorBubble = document.createElement("div");
      errorBubble.className = "bubble bot";
      errorBubble.innerText = "⚠️ Lỗi khi gọi chatbot.";
      chatBox.appendChild(errorBubble);
    }

    input.value = "";
    chatBox.scrollTop = chatBox.scrollHeight;
  });
});
