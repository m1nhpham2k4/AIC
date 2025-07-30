document.addEventListener("DOMContentLoaded", async () => {
  const keyframesSubfolders = document.getElementById("keyframes-subfolders");

  try {
    const res = await fetch("/folder-json");
    const data = await res.json();

    for (const folder of data.folders) {
      for (const sub of data.subfolders_map[folder]) {
        const li = document.createElement("li");
        li.className = "subfolder-item";
        li.textContent = sub;

        // ✅ Điều hướng đến /keyframes/L01_V001
        li.addEventListener("click", () => {
          window.location.href = `/keyframes/${sub}`;
        });

        keyframesSubfolders.appendChild(li);
      }
    }

    keyframesSubfolders.classList.remove("collapsed");
    keyframesSubfolders.classList.add("expanded");
  } catch (err) {
    console.error("❌ Lỗi khi fetch /folder-json:", err);
  }
});
