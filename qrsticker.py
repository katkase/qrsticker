#!/usr/bin/env python3
"""
qrsticker.py — colloca un QR code su una cover quadrata per adesivi.

Default tarati sul progetto Gattaplayer: adesivo 9,3 cm, moduli in bianco
caldo direttamente sul fondo (senza campo bianco), angolo in alto a destra
e in basso a sinistra, margine stile albo Marvel.

Esempi
------
  # default: due posizioni, due link, dimensione automatica
  python3 qrsticker.py cover.png \\
      --album https://open.spotify.com/album/XXXX \\
      --track https://open.spotify.com/track/YYYY

  # variante con campo bianco e codice rosso scuro
  python3 qrsticker.py cover.png --album https://... --field on

  # dimensione forzata, solo alto a destra
  python3 qrsticker.py cover.png --album https://... --size 2.5 --position tr
"""

import argparse
import os
import sys
from collections import Counter

import qrcode
from PIL import Image, ImageDraw, ImageOps

WARM_WHITE = (0xFA, 0xF6, 0xF0)
DARK_RED = (0x8A, 0x0E, 0x0E)

EC = {
    'L': qrcode.constants.ERROR_CORRECT_L,
    'M': qrcode.constants.ERROR_CORRECT_M,
    'Q': qrcode.constants.ERROR_CORRECT_Q,
    'H': qrcode.constants.ERROR_CORRECT_H,
}


def sample_background(im, samples=4000):
    """Colore di fondo dominante, campionato dai quattro angoli."""
    w, h = im.size
    box = int(min(w, h) * 0.08)
    px = []
    for (x0, y0) in [(0, 0), (w - box, 0), (0, h - box), (w - box, h - box)]:
        step = max(1, box // 20)
        for x in range(x0, x0 + box, step):
            for y in range(y0, y0 + box, step):
                px.append(im.getpixel((x, y)))
                if len(px) >= samples:
                    break
    return Counter(px).most_common(1)[0][0]


def figure_edge(im, bg, band, side, tol=55):
    """
    Bordo della figura dentro una fascia orizzontale.
    side 'left'  -> x minimo in cui compare la figura
    side 'right' -> x massimo
    Restituisce None se la fascia e' tutta fondo pulito.
    """
    w, h = im.size
    y0, y1 = band
    hits = []

    def is_fig(p):
        return sum(abs(a - b) for a, b in zip(p, bg)) > tol * 2

    xs = range(0, int(w * 0.65), 3) if side == 'left' else range(w - 1, int(w * 0.35), -3)
    for y in range(max(0, y0), min(h, y1), 12):
        for x in xs:
            if is_fig(im.getpixel((x, y))):
                hits.append(x)
                break
    if not hits:
        return None
    return (min(hits) if side == 'left' else max(hits))


def build_matrix(url, ec='M'):
    q = qrcode.QRCode(error_correction=EC[ec], border=4)
    q.add_data(url)
    q.make(fit=True)
    return q.get_matrix(), q.version, q.modules_count


def fits(im, bg, ppc, foot_cm, inset_cm, corner):
    """True se il footprint sta su fondo pulito in quell'angolo."""
    w, h = im.size
    foot = int(foot_cm * ppc)
    ins = int(inset_cm * ppc)
    if corner == 'tr':
        band = (ins, ins + foot)
        edge = figure_edge(im, bg, band, 'right')
        if edge is None:
            return True
        return (w - ins - foot) > edge + 0.03 * ppc
    else:
        band = (h - ins - foot, h - ins)
        edge = figure_edge(im, bg, band, 'left')
        if edge is None:
            return True
        return (ins + foot) < edge - 0.03 * ppc


def autosize(im, bg, ppc, inset_cm, corner, n, cap, min_module_mm):
    """Massimo footprint che sta su fondo pulito, senza scendere sotto il modulo minimo."""
    f = cap
    while f >= 1.5:
        module_mm = f * 10.0 / n
        if module_mm < min_module_mm:
            return None, module_mm
        if fits(im, bg, ppc, f, inset_cm, corner):
            return round(f, 2), module_mm
        f -= 0.05
    return None, 0


def render(im, matrix, n, ppc, foot_cm, inset_cm, corner, field, fg, field_col):
    out = im.copy()
    d = ImageDraw.Draw(out)
    w, h = out.size
    foot = int(round(foot_cm * ppc))
    ins = int(round(inset_cm * ppc))
    S = foot / n
    ox = (w - ins - foot) if corner == 'tr' else ins
    oy = ins if corner == 'tr' else (h - ins - foot)
    if field:
        d.rectangle([ox, oy, ox + foot - 1, oy + foot - 1], fill=field_col)
    for r in range(n):
        for c in range(n):
            if matrix[r][c]:
                d.rectangle([
                    ox + int(round(c * S)), oy + int(round(r * S)),
                    ox + int(round((c + 1) * S)) - 1, oy + int(round((r + 1) * S)) - 1
                ], fill=fg)
    return out, S / ppc * 10.0


def verify(img, inverted):
    """Decodifica di controllo. Se il codice e' invertito, inverte prima di leggere."""
    try:
        import cv2
        import numpy as np
        from pyzbar.pyzbar import decode as zdec
    except ImportError:
        return 'decoder non installati (pip install opencv-python-headless pyzbar)'
    res = []
    for w in (1500, 900, 600):
        s = img.resize((w, w), Image.LANCZOS)
        if inverted:
            s = ImageOps.invert(s)
        a = cv2.cvtColor(np.array(s), cv2.COLOR_RGB2BGR)
        t, _, _ = cv2.QRCodeDetector().detectAndDecode(a)
        z = zdec(s)
        res.append(f"{w}px {'OK' if t else 'X'}/{'OK' if z else 'X'}")
    return '  '.join(res)


def main():
    p = argparse.ArgumentParser(description='Colloca un QR su una cover per adesivi.')
    p.add_argument('cover')
    p.add_argument('--album', help='URL album')
    p.add_argument('--track', help='URL brano')
    p.add_argument('--url', action='append', default=[], help='URL generico, ripetibile')
    p.add_argument('--sticker-cm', type=float, default=9.3)
    p.add_argument('--position', choices=['tr', 'bl', 'both'], default='both')
    p.add_argument('--field', choices=['on', 'off'], default='off',
                   help="on = campo chiaro sotto il codice; off = moduli chiari sul fondo")
    p.add_argument('--size', default='auto', help="footprint in cm, oppure 'auto'")
    p.add_argument('--max-size', type=float, default=2.8)
    p.add_argument('--inset-mm', type=float, default=None,
                   help='margine dai bordi; default 3.5 con campo, 2.0 senza')
    p.add_argument('--ec', choices=list(EC), default='M')
    p.add_argument('--min-module', type=float, default=0.53, help='modulo minimo in mm')
    p.add_argument('--outdir', default='.')
    p.add_argument('--prefix', default='qr')
    args = p.parse_args()

    field = args.field == 'on'
    inset_cm = (args.inset_mm if args.inset_mm is not None else (3.5 if field else 2.0)) / 10.0

    im = Image.open(args.cover).convert('RGB')
    if im.width != im.height:
        print('attenzione: la cover non e\' quadrata, i calcoli assumono 1:1', file=sys.stderr)
    ppc = im.width / args.sticker_cm
    bg = sample_background(im)

    fg = DARK_RED if field else WARM_WHITE
    targets = []
    if args.album:
        targets.append(('album', args.album))
    if args.track:
        targets.append(('track', args.track))
    targets += [(f'url{i+1}', u) for i, u in enumerate(args.url)]
    if not targets:
        p.error('serve almeno un URL (--album / --track / --url)')

    corners = ['tr', 'bl'] if args.position == 'both' else [args.position]
    os.makedirs(args.outdir, exist_ok=True)

    print(f"cover {im.width}px  {args.sticker_cm}cm  {ppc:.1f}px/cm")
    print(f"fondo campionato #{bg[0]:02X}{bg[1]:02X}{bg[2]:02X}   "
          f"campo {'chiaro' if field else 'assente'}   inset {inset_cm*10:.1f}mm   EC {args.ec}\n")

    for label, url in targets:
        matrix, ver, mods = build_matrix(url, args.ec)
        n = len(matrix)
        print(f"[{label}] {len(url)} car.  versione {ver}  {mods} moduli (+8 quiet = {n})")
        for corner in corners:
            if args.size == 'auto':
                foot, mm = autosize(im, bg, ppc, inset_cm, corner, n, args.max_size, args.min_module)
                if foot is None:
                    print(f"   {corner}: nessuna dimensione utile "
                          f"(modulo scenderebbe sotto {args.min_module}mm) — accorcia l'URL\n")
                    continue
            else:
                foot = float(args.size)
                if not fits(im, bg, ppc, foot, inset_cm, corner) and not field:
                    print(f"   {corner}: ATTENZIONE, {foot}cm invade la figura")
            img, mm = render(im, matrix, n, ppc, foot, inset_cm, corner, field, fg, WARM_WHITE)
            name = f"{args.prefix}_{label}_{corner}_{foot:.2f}cm.png"
            path = os.path.join(args.outdir, name)
            img.save(path, dpi=(ppc * 2.54, ppc * 2.54))
            flag = '' if mm >= 0.6 else '  <-- modulo stretto, provalo sul campo'
            print(f"   {corner}: {foot:.2f}cm  modulo {mm:.3f}mm{flag}")
            print(f"      {verify(img, inverted=not field)}")
            print(f"      -> {path}")
        print()


if __name__ == '__main__':
    main()
