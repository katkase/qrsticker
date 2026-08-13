# qrsticker

Place a QR code on square cover art without covering the artwork.

Built for printing stickers. The script measures how much clean background
the cover actually has in a given corner, picks the largest code that fits,
and verifies the result is decodable before you send anything to print.

Output is a PNG at the source resolution with correct DPI written into the
metadata.

## Why

A QR code that looks fine on screen can be unreadable on a 3 cm sticker.
What matters is the *module* — the elementary square of the code — not the
overall size. Long URLs and high error correction both push the module
smaller. Below roughly 0.5 mm, scanning starts failing on modest cameras
and in poor light, which is exactly where street stickers live.

This script makes that tradeoff explicit instead of leaving it to chance.

## Installation

Python 3.9 or later.

### Windows

```
py -m venv .venv
.venv\Scripts\activate
pip install qrcode pillow opencv-python-headless pyzbar
```

The zbar C library ships inside the `pyzbar` wheel on Windows, so there is
nothing else to install.

### Linux / macOS

```
python3 -m venv .venv
source .venv/bin/activate
pip install qrcode pillow opencv-python-headless pyzbar
```

`pyzbar` is only a binding — the actual decoder is a system library:

```
sudo apt install libzbar0        # Debian / Ubuntu
brew install zbar                # macOS
sudo emerge media-gfx/zbar       # Gentoo
```

Without it, `import pyzbar` fails when loading the shared library. The
error looks like a broken pip package but is not.

### Dependencies

| Package | Purpose |
|---|---|
| `qrcode` | generates the code matrix |
| `pillow` | reads and composites images |
| `opencv-python-headless` | decode verification (optional) |
| `pyzbar` | second verification decoder (optional) |

Both optional packages can be skipped — the script still generates files
and prints a note instead of the verification report. Use the `headless`
OpenCV build; the regular one pulls in the whole Qt GUI stack for nothing.

## Usage

```
python qrsticker.py cover.png --album "https://open.spotify.com/album/XXXX"
```

Two destinations at once, useful for A/B testing which one performs:

```
python qrsticker.py cover.png --album "https://open.spotify.com/album/XXXX" --track "https://open.spotify.com/track/YYYY"
```

Always quote URLs. In PowerShell the line continuation is a backtick, in
`cmd` it is `^` — when in doubt keep it on one line.

### Options

| Option | Default | Description |
|---|---|---|
| `--album URL` | — | album destination |
| `--track URL` | — | track destination |
| `--url URL` | — | generic destination, repeatable |
| `--sticker-cm` | `9.3` | printed sticker side, in cm |
| `--position` | `both` | `tr` top right, `bl` bottom left, `both` |
| `--field` | `off` | `off` light modules on the artwork; `on` light panel with dark modules |
| `--size` | `auto` | footprint in cm, or `auto` |
| `--max-size` | `2.8` | ceiling for the automatic search |
| `--inset-mm` | `3.5` with panel, `2.0` without | margin from the edges |
| `--ec` | `M` | error correction: `L` `M` `Q` `H` |
| `--min-module` | `0.53` | smallest accepted module, in mm |
| `--outdir` | `.` | output directory |
| `--prefix` | `qr` | output filename prefix |

Colour constants (`WARM_WHITE`, `DARK_RED`) are at the top of the file.

### The two visual modes

**`--field off`** (default) draws the modules in warm white directly on the
cover background, with no panel. The quiet zone is clean background rather
than white. This produces an *inverted* code relative to the spec: recent
iPhones and Android phones read it, some third-party apps and older Android
devices do not. Test it in the field before printing a run.

**`--field on`** draws a light panel with dark red modules, 3.5 mm from the
edges, in the style of the barcode box on comic books. Standard polarity,
so anything reads it. This is the safe option.

## How sizing works

In `auto` mode the script starts at `--max-size` and steps down by 0.5 mm
until the footprint sits entirely on clean background. The subject edge is
measured row by row inside the band the code would actually occupy — not
against a fixed crop — so it adapts to the composition.

If fitting the available space would push the module below `--min-module`,
the script stops and says so rather than emitting a file that would not
scan. When that happens: shorten the URL, try the other corner, or switch
to `--field on`, which has no clearance constraint because the panel is
allowed to sit on top of the subject.

The background colour is sampled from the four corners, so the script is
not tied to any particular artwork palette.

## Verification

Every generated file is read back with two independent decoders at three
decreasing resolutions, simulating an imperfect photo. Inverted codes are
inverted before decoding — otherwise they would always fail on polarity
and the check would tell you nothing about geometry, contrast and margins,
which are the things that actually break.

A warning is printed below 0.6 mm module size. It does not mean the code
fails; it means the margin thins out with dirt, scratches and low light.

## Rules of thumb

Reading distance is roughly ten times the code's side: a 2 cm code scans
from about 20 cm, which is the distance someone reaches by leaning in
slightly. Below that people do not bother.

Shortening the URL buys more than enlarging the sticker. On a Spotify link,
dropping `?si=...` and `&utm_source=...` removes about thirty characters and
drops the code a full version, at identical physical size.

Embedding a logo forces error correction H, which inflates the matrix
substantially. On small stickers the logo costs more legibility than it
adds recognition.

## Known limitations

Edge detection compares each pixel against the sampled background colour
with a fixed tolerance. On covers with broad gradients, or where the
subject is close in colour to the background, the measurement can be wrong
— force `--size` and check the result visually. On flat backgrounds it is
reliable.

The script assumes square cover art. If it is not, a warning is printed and
all calculations are based on the width.

## License

MIT.
