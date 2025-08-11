let currentItems = [];

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

    container.innerHTML = `<li style="padding:6px 8px;color:#666;">🔄 Đang tải...</li>`;

    try {
      const res = await fetch("/api/keyframes-tree");
      if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
      const data = await res.json();

      container.innerHTML = "";

      (data.keyframes || []).forEach(group => {
        const parentLi = document.createElement("li");
        parentLi.classList.add("subfolder");

        const folderBtn = document.createElement("button");
        folderBtn.type = "button";
        folderBtn.className = "folder-toggle";
        folderBtn.textContent = group.name;
        folderBtn.style.cursor = "pointer";

        const subUl = document.createElement("ul");
        subUl.classList.add("sub-subfolders");
        subUl.style.display = "none";

        (group.subfolders || []).forEach(sub => {
          const subLi = document.createElement("li");
          subLi.classList.add("subfolder-item");
          subLi.style.cursor = "pointer";

          const subBtn = document.createElement("button");
          subBtn.type = "button";
          subBtn.textContent = sub;
          subBtn.style.all = "unset";
          subBtn.style.cursor = "pointer";
          subBtn.addEventListener("click", () => loadImages(group.name, sub));

          subLi.appendChild(subBtn);
          subUl.appendChild(subLi);
        });

        folderBtn.addEventListener("click", () => {
          subUl.style.display = subUl.style.display === "none" ? "block" : "none";
        });

        parentLi.appendChild(folderBtn);
        parentLi.appendChild(subUl);
        container.appendChild(parentLi);
      });

      container.classList.remove("collapsed");
      container.classList.add("expanded");
    } catch (err) {
      console.error("❌ Lỗi khi tải cây thư mục:", err);
      container.innerHTML = `<li style="padding:6px 8px;color:#c00;">❌ Lỗi khi tải cây thư mục</li>`;
    }
  });
});

// ========================== LOAD IMAGES ==========================
async function loadImages(folder, subfolder, offset = 0, limit = 0) {
  const preview = document.getElementById("preview");
  if (!preview) return;

  preview.innerHTML = "<p>🔄 Đang tải ảnh...</p>";

  try {
    const url = `/api/keyframes-images?folder=${encodeURIComponent(folder)}&subfolder=${encodeURIComponent(subfolder)}&offset=${offset}&limit=${limit}`;
    const res = await fetch(url);
    if (!res.ok) throw new Error(`Server trả lỗi: ${res.status} ${res.statusText}`);

    const data = await res.json();

    currentItems = Array.isArray(data.items) ? data.items : [];
    const images = Array.isArray(data.images) ? data.images : [];

    preview.innerHTML = "";

    if (currentItems.length > 0) {
      // Render theo items (có n, pts_time)
      currentItems.forEach((it) => {
        const img = document.createElement("img");
        img.src = it.src;
        img.classList.add("thumbnail");
        if (it.n != null) img.dataset.n = String(it.n);
        if (it.pts_time != null) img.dataset.ptsTime = String(it.pts_time);
        img.addEventListener("click", () => showImageDetail(it, folder, subfolder));
        preview.appendChild(img);
      });
    } else if (images.length > 0) {
      // Fallback: render theo danh sách ảnh đơn thuần
      images.forEach((src) => {
        const img = document.createElement("img");
        img.src = src;
        img.classList.add("thumbnail");
        img.addEventListener("click", () =>
          showImageDetail({ src, n: null, pts_time: null }, folder, subfolder)
        );
        preview.appendChild(img);
      });
    } else {
      preview.innerHTML = "<p>❌ Không tìm thấy ảnh nào.</p>";
    }
  } catch (err) {
    console.error("⚠️ Lỗi khi fetch ảnh:", err);
    preview.innerHTML = "<p style='color:red;'>❌ Lỗi khi tải ảnh.</p>";
  }
}

// ========================== DETAIL (VIDEO/ẢNH) ==========================
async function showImageDetail(item, folder, subfolder) {
  const detailPanel = document.getElementById("image-detail");
  const previewContainer = detailPanel?.querySelector(".large-preview");
  const title = document.getElementById("image-title");
  const length = document.getElementById("image-length");
  const author = document.getElementById("image-author");
  const url = document.getElementById("image-url");

  if (!detailPanel || !previewContainer) return;

  detailPanel.classList.remove("hidden");

  // Metadata demo
  title.textContent = `Title: ${subfolder}`;
  length.textContent = "Length: ~";
  author.textContent = "Author: Unknown";
  url.href = "#";
  url.textContent = "#";

  // ⚠️ Backend /api/video-info mong đợi 'folder' chính là tên folder Keyframes_L0x
  try {
    const res = await fetch(
      `/api/video-info?folder=${encodeURIComponent(folder)}&subfolder=${encodeURIComponent(subfolder)}`
    );

    if (!res.ok) throw new Error("Không có video");

    const data = await res.json();
    const videoUrl = data.video_url;

    previewContainer.innerHTML = `
      <video id="videoPlayer" controls width="100%">
        <source src="${videoUrl}" type="video/mp4" />
        Trình duyệt của bạn không hỗ trợ video.
      </video>
    `;

    const videoEl = document.getElementById("videoPlayer");
    await new Promise((resolve) => {
      const onLoaded = () => {
        videoEl.removeEventListener("loadedmetadata", onLoaded);
        resolve();
      };
      videoEl.addEventListener("loadedmetadata", onLoaded, { once: true });
      videoEl.load?.();
    });

    const t = (typeof item?.pts_time === "string") ? Number(item.pts_time) : item?.pts_time;
    if (typeof t === "number" && !Number.isNaN(t)) {
      videoEl.currentTime = t;
    }

    videoEl.play().catch(() => {});
  } catch (err) {
    console.warn("Video không tồn tại, hiển thị ảnh:", err);
    const src = item?.src || "";
    previewContainer.innerHTML = `<img id="large-image" src="${src}" alt="Preview" />`;
  }
}
