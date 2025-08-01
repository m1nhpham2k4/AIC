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
                console.log(sub)
                const imgRes = await fetch(`/images/${sub}`);

                const imgData = await imgRes.json();


                imgData.images.forEach(url => {
                  const img = document.createElement("img");
                  img.src = url;
                  img.className = "img_show_info";
                  img.alt = sub;
                  img.style.width = "250px";
                  img.style.height = "250px";
                  img.style.objectFit = "cover";
                  img.style.borderRadius = "6px";
                  img.style.margin = "6px";
                  // tạo 1 khung để xem thông tin 
                  img.addEventListener("click", () => {
                      const div = document.createElement("div");
                      div.style.position = "absolute";        
                      div.style.top = "21px";            // khoảng cách từ trên xuống
                      div.style.right = "20px";            // sát mép phải
                      div.style.width = "585px";
                      div.style.height = "900px";
                      div.id = "image_infomation"
                      div.style.backgroundColor = "#ADD8E6";
                      div.style.borderRadius = "6px";
                      // Tạo ảnh
                      const img = document.createElement("img");
                      img.src = url;
                      img.className = "img_show_info";
                      img.alt = sub;
                      img.style.width = "585px";

                      img.style.height = "350px";
                      img.style.objectFit = "cover";
                      img.style.borderRadius = "6px";
                      // Tạo khu vực thoát
                      const div_thoat = document.createElement("div");
                      div_thoat.style.position = "relative";       
                      div_thoat.style.width = "585px";
                      div_thoat.style.height = "40px";
                      // Thêm ảnh thoát trong kv thoát
                      const img_thoat = document.createElement("img");
                      img_thoat.src = "../static/images/Exit.png";
                      img_thoat.style.position = "absolute";   // ✅ Gán qua style           
                      img_thoat.style.right = "0px";           // 👈 Dịch sát mép phải
                      img_thoat.style.width = "35px";
                      img_thoat.style.height = "35px";
                      img_thoat.addEventListener("click",()=>{
                        preview.removeChild(document.getElementById("image_infomation"))
                      })
                      // div để trữ thông tin
                      const div_thong_tin = document.createElement("div")
                      // tiêu đề, tác giả, độ dài, đường dẫn
                      // tiêu đề
                      const title = document.createElement("h2");
                      title.style.paddingTop = "50px"
                      title.style.paddingLeft = "30px"
                      title.textContent ="Tiêu Đề: "
                      // tác giả
                      const author = document.createElement("h2");
                      author.style.paddingTop = "50px"
                      author.style.paddingLeft = "30px"
                      author.textContent ="Tác Giả: "
                      // độ dài
                      const length = document.createElement("h2");
                      length.style.paddingTop = "50px"
                      length.style.paddingLeft = "30px"
                      length.textContent ="Độ Dài Video: "
                      // đường dẫn
                      const directory = document.createElement("h2");
                      directory.style.paddingTop = "50px"
                      directory.style.paddingLeft = "30px"
                      directory.textContent ="Đường dẫn video: "
                      //
                      div_thong_tin.appendChild(title)
                      div_thong_tin.appendChild(author)
                      div_thong_tin.appendChild(length)
                      div_thong_tin.appendChild(directory)
                      //
                      div_thoat.appendChild(img_thoat)
                      div.appendChild(div_thoat)
                      div.appendChild(img)
                      div.appendChild(div_thong_tin)
                      preview.appendChild(div)
                  });

                  preview.appendChild(img);


                });
              } catch (err) {
                preview.innerHTML = "<p style='color:red;'>Không thể tải ảnh</p>"
                console.log(err);
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
  scrollToBottom();

  input.value = "";
  input.focus();  // ✅ tự động focus lại input sau khi gửi

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

  scrollToBottom();  // ✅ Cuộn xuống sau khi hiển thị bot reply
  });
});

function scrollToBottom() {
  const chatHistory = document.getElementById('chat-history');
  chatHistory.scrollTop = chatHistory.scrollHeight;
}

