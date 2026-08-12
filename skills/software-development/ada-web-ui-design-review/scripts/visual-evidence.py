#!/usr/bin/env python3
"""Visual evidence from screenshots when no vision provider is available.

Usage:
  python visual-evidence.py <png...>
  python visual-evidence.py --contrast '#e6a817' '#ffffff' '#ff6b1a' '#ffffff'

Modes:
  default          Per image: size, color budget (top colors), saturated-accent
                   count, and horizontal content bands (panel/whitespace layout).
  --contrast       WCAG contrast ratio(s) for hex pairs (foreground background).
"""
import collections
import sys

try:
    from PIL import Image
except ImportError:
    print("PIL required: pip install pillow", file=sys.stderr)
    sys.exit(1)


def wcag_luminance(hex_color):
    h = hex_color.lstrip('#')
    r, g, b = (int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4))

    def f(c):
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4

    return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b)


def wcag_ratio(fg, bg):
    l1, l2 = wcag_luminance(fg), wcag_luminance(bg)
    if l1 < l2:
        l1, l2 = l2, l1
    return (l1 + 0.05) / (l2 + 0.05)


def content_bands(im, step=4, threshold=0.1):
    w, h = im.size
    px = im.convert('RGB').load()
    bg = im.getpixel((0, 0))
    bands, cur_start = [], None
    for y in range(0, h, step):
        non_bg = sum(
            1 for x in range(0, w, 8)
            if abs(px[x, y][0] - bg[0]) + abs(px[x, y][1] - bg[1]) + abs(px[x, y][2] - bg[2]) > 40
        )
        frac = non_bg / max(w // 8, 1)
        if frac > threshold and cur_start is None:
            cur_start = y
        elif frac <= threshold and cur_start is not None:
            bands.append((cur_start, y))
            cur_start = None
    if cur_start is not None:
        bands.append((cur_start, h))
    return [b for b in bands if b[1] - b[0] >= 8]


def analyze_image(path):
    im = Image.open(path).convert('RGB')
    w, h = im.size
    small = im.resize((max(1, w // 4), max(1, h // 4)))
    colors = collections.Counter(small.getdata())
    top = [(f'#{r:02x}{g:02x}{b:02x}', n) for (r, g, b), n in colors.most_common(8)]
    sat = [(f'#{r:02x}{g:02x}{b:02x}', n) for (r, g, b), n in colors.most_common(500)
           if max(r, g, b) - min(r, g, b) > 50]
    print(f'== {path} ({w}x{h})')
    print(f'   top colors: {top}')
    print(f'   saturated accents ({len(sat)}): {sat[:5]}')
    print(f'   content bands (y ranges): {content_bands(im)}')


def main():
    if '--contrast' in sys.argv:
        i = sys.argv.index('--contrast')
        pairs = sys.argv[i + 1:]
        for j in range(0, len(pairs) - 1, 2):
            fg, bg = pairs[j], pairs[j + 1]
            r = wcag_ratio(fg, bg)
            verdict = 'PASS' if r >= 4.5 else ('LARGE-TEXT' if r >= 3.0 else 'FAIL')
            print(f'{fg} on {bg}: {r:.2f}:1  {verdict}')
        return
    for path in sys.argv[1:]:
        analyze_image(path)


if __name__ == '__main__':
    main()
