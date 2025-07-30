document.addEventListener("DOMContentLoaded", () => {
  const keyframesBtn = document.getElementById("keyframes-btn");
  const keyframesSubfolders = document.getElementById("keyframes-subfolders");
  const preview = document.getElementById("image-preview");
  const chatContainer = document.getElementById("chat-container");

  keyframesBtn.addEventListener("click", async () => {
    const isExpanded = keyframesSubfolders.classList.contains("expanded");
    keyframesSubfolders.innerHTML = "";

    if (isExpanded) {
      keyframesSubfolders.classList.remove("expanded");
      keyframesSubfolders.classList.add("collapsed");
    } else {
      try {
        const res = await fetch("/folder-json");
        const data = await res.json();

        for (const folder of data.folders) {
          for (const sub of data.subfolders_map[folder]) {
            const li = document.createElement("li");
            li.className = "subfolder-item";
            li.textContent = sub;

            li.addEventListener("click", async () => {
              chatContainer?.classList.add("hidden");
              preview.classList.add("image-visible");
              preview.innerHTML = "";

              try {
                const imgRes = await fetch(`/images/${sub}`);
                const imgData = await imgRes.json();

                imgData.images.forEach(url => {
                  const img = document.createElement("img");
                  img.src = url;
                  img.alt = sub;
                  img.style.width = "250px";
                  img.style.height = "250px";
                  img.style.objectFit = "cover";
                  img.style.borderRadius = "6px";
                  img.style.margin = "6px";
                  preview.appendChild(img);
                });
              } catch (err) {
                preview.innerHTML = "<p style='color:red;'>Không thể tải ảnh</p>";
              }
            });

            keyframesSubfolders.appendChild(li);
          }
        }

        keyframesSubfolders.classList.remove("collapsed");
        keyframesSubfolders.classList.add("expanded");
      } catch (err) {
        console.error("❌ Lỗi khi fetch JSON:", err);
      }
    }
  });

  // Chatbot
  const form = document.getElementById("chat-form");
  const input = document.getElementById("chat-input");
  const chatBox = document.getElementById("chat-history");
  const greeting = document.querySelector(".center-greeting");

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const message = input.value.trim();
    if (!message) return;

    greeting?.classList.add("hidden");

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
