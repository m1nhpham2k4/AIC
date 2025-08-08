document.addEventListener("DOMContentLoaded", () => {
  const keyframesBtn = document.getElementById("keyframes-btn");
  const container = document.getElementById("keyframes-subfolders");

  if (!keyframesBtn || !container) return;

  keyframesBtn.addEventListener("click", async () => {
    const isExpanded = container.classList.contains("expanded");

    if (isExpanded) {
      container.innerHTML = "";
      container.classList.remove("expanded");
      container.classList.add("collapsed");
      return;
    }

    try {
      const res = await fetch("/api/keyframes-tree");
      const data = await res.json();

      container.innerHTML = "";

      data.keyframes.forEach(group => {
        const parentLi = document.createElement("li");
        parentLi.classList.add("subfolder");

        const folderSpan = document.createElement("span");
        folderSpan.textContent = group.name;
        folderSpan.classList.add("folder-toggle");
        folderSpan.style.cursor = "pointer";

        const subUl = document.createElement("ul");
        subUl.classList.add("sub-subfolders");
        subUl.style.display = "none";

        group.subfolders.forEach(sub => {
          const subLi = document.createElement("li");
          subLi.textContent = sub;
          subLi.classList.add("subfolder-item");
          subLi.style.cursor = "pointer";

          // ✅ Khi click vào L01_V001 → load ảnh
          subLi.addEventListener("click", () => {
            loadImages(group.name, sub);
          });

          subUl.appendChild(subLi);
        });

        // Toggle hiển thị thư mục con
        folderSpan.addEventListener("click", () => {
          subUl.style.display = subUl.style.display === "none" ? "block" : "none";
        });

        parentLi.appendChild(folderSpan);
        parentLi.appendChild(subUl);
        container.appendChild(parentLi);
      });

      container.classList.remove("collapsed");
      container.classList.add("expanded");
    } catch (err) {
      console.error("❌ Lỗi khi tải cây thư mục:", err);
    }
  });
});

// ✅ Hàm load ảnh từ thư mục
async function loadImages(folder, subfolder) {
  const preview = document.getElementById("preview");
  preview.innerHTML = "<p>🔄 Đang tải ảnh...</p>";

  try {
    const res = await fetch(`/api/keyframes-images?folder=${folder}&subfolder=${subfolder}`);

    if (!res.ok) {
      throw new Error(`Lỗi từ server: ${res.status} ${res.statusText}`);
    }

    const data = await res.json();

    preview.innerHTML = "";

    if (data.images.length === 0) {
      preview.innerHTML = "<p>❌ Không tìm thấy ảnh nào.</p>";
      return;
    }

    data.images.forEach((src) => {
      const img = document.createElement("img");
      img.src = src;
      img.classList.add("thumbnail");
      img.addEventListener("click", () => {
        showImageDetail(src, folder, subfolder);  // 🟢 Gọi hàm khi click
      });
      preview.appendChild(img);
    });
  } catch (err) {
    preview.innerHTML = "<p style='color:red;'>❌ Lỗi khi tải ảnh.</p>";
    console.error("⚠️ Lỗi khi fetch ảnh:", err);
  }
}

async function showImageDetail(imageSrc, folder, subfolder) {
  const detailPanel = document.getElementById("image-detail");
  const previewContainer = detailPanel.querySelector(".large-preview");
  const title = document.getElementById("image-title");
  const length = document.getElementById("image-length");
  const author = document.getElementById("image-author");
  const url = document.getElementById("image-url");

  detailPanel.classList.remove("hidden");

  // 📝 Giả lập metadata
  title.textContent = `Title: ${subfolder}`;
  length.textContent = "Length: ~";
  author.textContent = "Author: Unknown";
  url.href = "#";
  url.textContent = "#";

  // Gọi API kiểm tra có video không
  try {
    const videoFolder = `Videos_${subfolder.split("_")[0]}`;
    const res = await fetch(`/api/video-info?folder=${videoFolder}&subfolder=${subfolder}`);

    if (!res.ok) throw new Error("Không có video");

    const data = await res.json();
    const videoUrl = data.video_url;

    previewContainer.innerHTML = `
      <video controls width="100%">
        <source src="${videoUrl}" type="video/mp4" />
        Trình duyệt của bạn không hỗ trợ video.
      </video>
    `;
  } catch (err) {
    // ❌ Không có video → fallback về ảnh
    console.warn("Video không tồn tại. Hiển thị ảnh thay thế.");
    previewContainer.innerHTML = `<img id="large-image" src="${imageSrc}" alt="Preview" />`;
  }
}

