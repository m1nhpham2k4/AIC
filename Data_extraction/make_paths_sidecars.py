#!/usr/bin/env python3
"""
make_paths_sidecars_v2.py  (fixed)

- Tạo <stem>.paths.txt cạnh mỗi <stem>.npy
- Tìm thư mục ảnh tương ứng ở bất kỳ đâu dưới --images-root theo --pattern (có {stem})
- Nếu nhiều thư mục khớp, chọn thư mục có nhiều ảnh nhất
- Ghi danh sách đường dẫn ảnh (ưu tiên tương đối; fallback tuyệt đối)
"""

import argparse
from pathlib import Path
from typing import List

def list_images(folder: Path, exts: List[str]) -> List[Path]:
    items: List[Path] = []
    for ext in exts:
        items.extend([p for p in folder.glob(f"*{ext}") if p.is_file()])
    return sorted(items, key=lambda p: p.name.lower())

def find_candidate_dirs(images_root: Path, stem: str, pattern: str) -> List[Path]:
    if pattern:
        pat = pattern.format(stem=stem)
        return [p for p in images_root.glob(pat) if p.is_dir()]
    return []

def fallback_find_by_name(images_root: Path, stem: str) -> List[Path]:
    return [p for p in images_root.rglob(stem) if p.is_dir() and p.name == stem]

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--npys-root", type=str, required=True, help="Folder containing <stem>.npy files")
    p.add_argument("--images-root", type=str, required=True, help="Root containing image directories (searched recursively)")
    p.add_argument("--img-ext", type=str, nargs="+", default=[".jpg", ".jpeg", ".png"], help="Image extensions to include")
    p.add_argument("--pattern", type=str, default="{stem}", help="Glob under images-root; use {stem}, e.g. '**/keyframes/{stem}/'")
    p.add_argument("--overwrite", action="store_true")
    args = p.parse_args()

    npys_root = Path(args.npys_root)
    images_root = Path(args.images_root)

    npys = sorted(npys_root.glob("*.npy"))
    if not npys:
        print(f"No .npy files found in {npys_root}")
        return

    for npy in npys:
        stem = npy.stem
        out_txt = npy.with_suffix('').with_suffix('.paths.txt')
        if out_txt.exists() and not args.overwrite:
            print(f"Exists, skip: {out_txt.name}")
            continue

        # 1) theo pattern
        candidates = find_candidate_dirs(images_root, stem, args.pattern)
        # 2) fallback theo tên folder
        if not candidates:
            candidates = fallback_find_by_name(images_root, stem)

        if not candidates:
            print(f"Skip {npy.name}: could not find a directory for stem '{stem}' under {images_root}")
            continue

        # Chọn thư mục có nhiều ảnh nhất
        best_dir = None
        best_imgs: List[Path] = []
        for c in candidates:
            imgs = list_images(c, args.img_ext)
            if len(imgs) > len(best_imgs):
                best_imgs = imgs
                best_dir = c

        if not best_dir or not best_imgs:
            print(f"Skip {npy.name}: matched dirs had no images with given extensions.")
            continue

        # Ghi danh sách path:
        # - ưu tiên relative với images_root (dễ đọc/di chuyển)
        # - nếu không relative được thì dùng absolute để tránh lỗi
        rel_lines: List[str] = []
        for img in best_imgs:
            try:
                rel = img.relative_to(images_root).as_posix()
                rel_lines.append(rel)
            except Exception:
                rel_lines.append(img.resolve().as_posix())

        out_txt.write_text("\n".join(rel_lines), encoding="utf-8")
        print(f"Wrote {out_txt.name} ({len(rel_lines)} lines) -> {best_dir.relative_to(images_root)}")

    print("Done.")

if __name__ == "__main__":
    main()
