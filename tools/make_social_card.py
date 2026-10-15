#!/usr/bin/env python3
"""Render the repository's social preview card (1280x640).

GitHub has no API for the social preview image, so this writes a PNG that has to
be uploaded by hand at Settings -> General -> Social preview.
"""
import json
import os
import pathlib

from PIL import Image, ImageDraw, ImageFont

ROOT = pathlib.Path(os.environ.get("OAI_AUDIT_ROOT", "/Users/dereky/oai-math"))
W, H, M = 1280, 640, 68

BG, INK, INK2, INK3 = "#eef1f5", "#0f151c", "#4d5a68", "#78859a"
RULE, AMBER, TEAL = "#d5dce4", "#9a5b06", "#0d6e56"

F = ROOT / "fonts"
serif = lambda s: ImageFont.truetype(str(F / "Newsreader.ttf"), s)
mono = lambda s: ImageFont.truetype(str(F / "IBMPlexMono-Regular.ttf"), s)
monob = lambda s: ImageFont.truetype(str(F / "IBMPlexMono-Medium.ttf"), s)
sans = lambda s: ImageFont.truetype(str(F / "IBMPlexSans.ttf"), s)


def tracked(d, xy, text, font, fill, gap):
    """Draw letter-spaced text, one glyph at a time."""
    x, y = xy
    for ch in text:
        d.text((x, y), ch, font=font, fill=fill)
        x += d.textlength(ch, font=font) + gap
    return x


def fit(d, text, mk, size, maxw):
    while size > 20:
        f = mk(size)
        if d.textlength(text, font=f) <= maxw:
            return f
        size -= 2
    return mk(size)


def main():
    data = json.loads((ROOT / "out" / "site_data.json").read_text(encoding="utf-8"))
    papers = [{"i": p["i"], "lean": data["flags"][p["d"]]["lean"]}
              for f in data["fams"] for p in f["m"]]
    papers.sort(key=lambda p: -p["i"])
    hubs = papers[:20]
    mx = hubs[0]["i"] or 1
    n_hub_lean = sum(1 for p in hubs if p["lean"])

    im = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(im)

    # kicker
    tracked(d, (M, 62), "OPENAI/MATH  ·  INDEPENDENT AUDIT  ·  2026-10-15",
            mono(20), INK3, 2.6)

    # headline
    l1, l2 = "The Lean coverage misses", "the load-bearing papers"
    fh = fit(d, l1, serif, 62, W - 2 * M)
    fh = min(fh.size, fit(d, l2, serif, 62, W - 2 * M).size)
    fh = serif(fh)
    d.text((M, 100), l1, font=fh, fill=INK)
    d.text((M, 100 + int(fh.size * 1.2)), l2, font=fh, fill=INK)

    # sub
    sub = ("719 manuscripts · 372 result families · 591 citations between them. "
           "The repository reports 42% formalized.")
    d.text((M, 268), sub, font=sans(24), fill=INK2)

    # stat row
    stats = [
        (f"{n_hub_lean} of 20", "most-cited papers with a Lean entry"),
        ("237 of 372", "families with no formalized member"),
        ("unchecked", "the catalogue's own review status"),
    ]
    x = M
    for i, (big, lab) in enumerate(stats):
        d.text((x, 322), big, font=monob(36), fill=INK if i == 2 else AMBER)
        d.text((x, 372), lab, font=mono(16), fill=INK3)
        x += 400

    # bar strip
    d.line([(M, 436), (W - M, 436)], fill=RULE, width=1)
    d.text((M, 452), "THE 20 MOST-CITED MANUSCRIPTS", font=mono(16), fill=INK3)
    url = "github.com/yuyauchuncn-dot/openai-math-audit"
    d.text((W - M - d.textlength(url, font=mono(15)), 452), url, font=mono(15), fill=INK3)

    bw = W - 2 * M
    y = 488
    for p in hubs:
        w = max(4, round(p["i"] / mx * bw))
        d.rectangle([M, y, M + w, y + 4], fill=TEAL if p["lean"] else AMBER)
        y += 6

    out = ROOT / "out" / "social-preview.png"
    im.save(out, "PNG", optimize=True)
    print(out, im.size, f"{out.stat().st_size / 1024:.0f} KB")
    print(f"top-20 with Lean: {n_hub_lean}, max in-degree: {mx}")


if __name__ == "__main__":
    main()
