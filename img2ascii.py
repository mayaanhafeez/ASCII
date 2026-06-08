#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageOps, ImageEnhance

# Detailed ramp (terminal-friendly)
DEFAULT_RAMP = " .'`^\",:;Il!i~+_-?][}{1)(|\\/tfjrxnuvczXYUJCLQ0OZmwqpdbkhao*#MW&8%B@$"

# Chat-friendly ramps (bold, high contrast)
CHAT_RAMP_BLOCKS = "█▓▒░ "
CHAT_RAMP_CLASSIC = "@#S%?*+;:,. "
CHAT_RAMP_SAFE = " .',;:!iltI1rjcfsxeznuvJCYXUZOQ0mwqbdkp8BW$M"


def apply_gamma(img_l: Image.Image, gamma: float) -> Image.Image:
    gamma = max(gamma, 1e-6)
    inv = 1.0 / gamma
    table = [int(((i / 255.0) ** inv) * 255) for i in range(256)]
    return img_l.point(table)


def compute_size(img_w: int, img_h: int, max_w: int, max_h: int, aspect: float) -> tuple[int, int]:
    # Effective height after terminal/chat character aspect correction
    eff_h = img_h * aspect
    scale_w = max_w / img_w
    scale_h = max_h / eff_h
    scale = min(scale_w, scale_h)
    new_w = max(1, int(img_w * scale))
    new_h = max(1, int(eff_h * scale))
    return new_w, new_h


def image_to_ascii(
    img: Image.Image,
    max_width: int,
    max_height: int,
    ramp: str,
    aspect: float,
    contrast: float,
    gamma: float,
    autocontrast_cutoff: int,
    dither: bool,
    double: bool,
) -> str:
    if not ramp:
        raise ValueError("ramp must be a non-empty string")

    # grayscale
    gray = img.convert("L")

    # improve visibility
    gray = ImageOps.autocontrast(gray, cutoff=autocontrast_cutoff)
    gray = ImageEnhance.Contrast(gray).enhance(max(0.0, contrast))
    gray = apply_gamma(gray, gamma)

    # resize to bounded box
    w, h = gray.size
    new_w, new_h = compute_size(w, h, max_width, max_height, aspect)
    gray = gray.resize((new_w, new_h), resample=Image.Resampling.LANCZOS)

    if dither:
        gray = gray.convert(
            "P",
            palette=Image.Palette.ADAPTIVE,
            colors=256,
            dither=Image.Dither.FLOYDSTEINBERG,
        ).convert("L")

    # map pixels -> chars
    n = len(ramp) - 1
    chars = [ramp[int((px / 255) * n)] for px in gray.getdata()]

    # build lines
    lines = []
    for i in range(0, len(chars), new_w):
        line = "".join(chars[i : i + new_w])
        if double:
            line = "".join(ch * 2 for ch in line)
        lines.append(line)

    return "\n".join(lines)


def image_to_colored(
    img: Image.Image,
    max_width: int,
    max_height: int,
    ramp: str,
    aspect: float,
    contrast: float,
    gamma: float,
    autocontrast_cutoff: int,
    dither: bool,
    double: bool,
    invert: bool = False,
) -> tuple[str, str]:
    """Return (plain_text, html_string) with per-character RGB colour spans."""
    gray = img.convert("L")
    if invert:
        gray = ImageOps.invert(gray)
    gray = ImageOps.autocontrast(gray, cutoff=autocontrast_cutoff)
    gray = ImageEnhance.Contrast(gray).enhance(max(0.0, contrast))
    gray = apply_gamma(gray, gamma)
    w, h = img.size
    new_w, new_h = compute_size(w, h, max_width, max_height, aspect)
    gray = gray.resize((new_w, new_h), resample=Image.Resampling.LANCZOS)
    if dither:
        gray = gray.convert(
            "P", palette=Image.Palette.ADAPTIVE, colors=256, dither=Image.Dither.FLOYDSTEINBERG
        ).convert("L")
    rgb = img.convert("RGB").resize((new_w, new_h), resample=Image.Resampling.LANCZOS)
    n = len(ramp) - 1
    gray_data = list(gray.getdata())
    rgb_data = list(rgb.getdata())
    plain_lines, html_lines = [], []
    for row in range(new_h):
        start = row * new_w
        plain_row, spans = [], []
        for col in range(new_w):
            idx = start + col
            ch = ramp[int((gray_data[idx] / 255) * n)]
            if double:
                ch = ch * 2
            plain_row.append(ch)
            r, g, b = rgb_data[idx]
            safe = ch.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            spans.append(f'<span style="color:#{r:02x}{g:02x}{b:02x}">{safe}</span>')
        plain_lines.append("".join(plain_row))
        html_lines.append("".join(spans))
    return "\n".join(plain_lines), "\n".join(html_lines)


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Image → ASCII (chat-friendly mode included)")
    ap.add_argument("image", type=Path)

    ap.add_argument("--max-width", type=int, default=80)
    ap.add_argument("--max-height", type=int, default=40)

    ap.add_argument("--aspect", type=float, default=0.55)
    ap.add_argument("--contrast", type=float, default=1.4)
    ap.add_argument("--gamma", type=float, default=0.8)
    ap.add_argument("--autocontrast-cutoff", type=int, default=1)
    ap.add_argument("--dither", action="store_true")
    ap.add_argument("--invert", action="store_true")

    ap.add_argument("--ramp", type=str, default=DEFAULT_RAMP, help="Custom ramp")

    # Chat options
    ap.add_argument("--chat", action="store_true", help="Print wrapped in code fences + use bold ramp defaults")
    ap.add_argument("--chat-ramp", choices=["blocks", "classic"], default="blocks",
                    help="Chat ramp preset (only used with --chat unless --ramp is set)")
    ap.add_argument("--double", action="store_true", help="Double characters horizontally (often looks better in chats)")

    return ap.parse_args()


def main() -> None:
    args = parse_args()

    if not args.image.exists():
        raise SystemExit(f"File not found: {args.image}")

    img = Image.open(args.image)

    if args.invert:
        img = ImageOps.invert(img.convert("L"))

    # choose ramp
    ramp = args.ramp
    if args.chat and args.ramp == DEFAULT_RAMP:
        ramp = CHAT_RAMP_BLOCKS if args.chat_ramp == "blocks" else CHAT_RAMP_CLASSIC

    ascii_art = image_to_ascii(
        img=img,
        max_width=args.max_width,
        max_height=args.max_height,
        ramp=ramp,
        aspect=args.aspect,
        contrast=args.contrast,
        gamma=args.gamma,
        autocontrast_cutoff=args.autocontrast_cutoff,
        dither=args.dither,
        double=args.double,
    )

    if args.chat:
        print("```txt")
        print(ascii_art)
        print("```")
    else:
        print(ascii_art)


if __name__ == "__main__":
    main()

