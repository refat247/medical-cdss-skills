"""
Lanczos-4 Figure Super-Resolution & Unsharp Masking Engine (publication copies only).

Writes enhanced copies to --output-dir; source figures are never modified.
Output format always matches the file extension (.png stays PNG, .jpg/.jpeg stay JPEG, .webp stays WebP).
Exit code 1 if any figure could not be processed.

NOTE: this file is kept byte-identical in cdss-retrieval-packager and cdss-bridge-note-publisher
(tests/test_claude_audit_fixes.py in each skill checks this).
"""

import argparse
import sys
from pathlib import Path

from PIL import Image, ImageEnhance, ImageFilter

IMG_EXTENSIONS = {".jpeg", ".jpg", ".png", ".webp"}
FORMAT_BY_EXT = {".jpeg": "JPEG", ".jpg": "JPEG", ".png": "PNG", ".webp": "WEBP"}


def _flatten_to_rgb(img: Image.Image) -> Image.Image:
    """Converts paletted / alpha / greyscale / CMYK images to RGB, compositing transparency over white."""
    if img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info):
        rgba = img.convert("RGBA")
        bg = Image.new("RGB", rgba.size, (255, 255, 255))
        bg.paste(rgba.convert("RGB"), mask=rgba.split()[3])
        return bg
    if img.mode in ("I;16", "I;16L", "I;16B", "I"):
        # Preserve 16-bit greyscale tonal values instead of clipping values >255 to white.
        return img.point(lambda v: v / 256).convert("L").convert("RGB")
    if img.mode != "RGB":
        return img.convert("RGB")
    return img


def _save(img: Image.Image, dst_path: Path) -> None:
    fmt = FORMAT_BY_EXT.get(dst_path.suffix.lower(), "PNG")
    dst_path.parent.mkdir(parents=True, exist_ok=True)
    if fmt == "JPEG":
        img.save(dst_path, format="JPEG", quality=95, dpi=(300, 300))
    elif fmt == "WEBP":
        img.save(dst_path, format="WEBP", quality=95)
    else:
        img.save(dst_path, format="PNG", dpi=(300, 300))


def enhance_figure(src_path: Path, dst_path: Path, scale_factor: int = 4) -> bool:
    """Upscales one figure with Lanczos resampling + unsharp masking + mild contrast lift."""
    try:
        with Image.open(src_path) as im:
            img = _flatten_to_rgb(im)
            new_size = (img.size[0] * scale_factor, img.size[1] * scale_factor)
            upscaled = img.resize(new_size, Image.Resampling.LANCZOS)
            sharpened = upscaled.filter(ImageFilter.UnsharpMask(radius=1.5, percent=125, threshold=3))
            enhanced = ImageEnhance.Contrast(sharpened).enhance(1.08)
            _save(enhanced, dst_path)
        return True
    except Exception as e:
        print(f"[ENHANCE-ERROR] Failed to enhance {src_path.name}: {e}", file=sys.stderr)
        return False


def audit_and_enhance_directory(figures_dir: Path, output_dir: Path, min_width: int = 600) -> dict:
    """Upscales figures narrower than min_width; copies the rest at 300 DPI. Returns counts incl. failures."""
    results = {"total": 0, "low_res": 0, "enhanced": 0, "copied": 0, "failed": 0}
    if not figures_dir.exists():
        return results
    output_dir.mkdir(parents=True, exist_ok=True)

    for img_path in sorted(figures_dir.glob("*.*")):
        if img_path.suffix.lower() not in IMG_EXTENSIONS:
            continue
        results["total"] += 1
        dst = output_dir / img_path.name
        try:
            with Image.open(img_path) as im:
                w = im.size[0]
            if w < min_width:
                results["low_res"] += 1
                if enhance_figure(img_path, dst, scale_factor=4 if w < 400 else 3):
                    results["enhanced"] += 1
                else:
                    results["failed"] += 1
            elif not dst.exists() or dst.stat().st_mtime < img_path.stat().st_mtime:
                with Image.open(img_path) as im:
                    img = im if dst.suffix.lower() == ".png" else _flatten_to_rgb(im)
                    _save(img, dst)
                results["copied"] += 1
        except Exception as e:
            results["failed"] += 1
            print(f"[AUDIT-WARN] Error processing {img_path}: {e}", file=sys.stderr)
    return results


def main():
    parser = argparse.ArgumentParser(description="CDSS Figure Resolution Auditor & Super-Resolution Engine")
    parser.add_argument("--figures-dir", "-f", required=True, help="Path to input figures directory")
    parser.add_argument("--output-dir", "-o", required=True, help="Path to enhanced figures output directory")
    parser.add_argument("--min-width", "-w", type=int, default=600, help="Minimum width threshold for upscaling")
    args = parser.parse_args()

    src, dst = Path(args.figures_dir), Path(args.output_dir)
    print(f"[FIGURE-AUDIT] Scanning {src} (threshold: {args.min_width}px)...")
    res = audit_and_enhance_directory(src, dst, min_width=args.min_width)
    print(f"[FIGURE-AUDIT] {res['total']} scanned | {res['enhanced']} upscaled | {res['copied']} copied | "
          f"{res['failed']} failed -> {dst}")
    sys.exit(1 if res["failed"] else 0)


if __name__ == "__main__":
    main()
