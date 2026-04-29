# ARTSEY for macOS (Karabiner)

ARTSEY left/right layout for macOS, implemented with Karabiner-Elements and tuned for MacBook use.

Unofficial Karabiner implementation of ARTSEY for macOS. Not affiliated with artsey.io.

Reference:
- [ARTSEY official site](https://artsey.io/)
- [Nick Pederson's `artsey_on_karabiner`](https://github.com/nickpedersen/artsey_on_karabiner)

This repository ships the recommended distribution format for Karabiner:
- `artsey_complex_modifications.json`

It does **not** require replacing your full `karabiner.json`. Users can import the rule file and enable only the rules they want.

## Why

ARTSEY is often explored through dedicated hardware, custom keypads, or soldered builds. One goal of this project is to lower that barrier for MacBook users by making ARTSEY usable as software on top of a standard macOS setup.

This is especially useful for people who want to try one-handed English input without buying or assembling new hardware, including users exploring ARTSEY because of accessibility needs, injury, or mobile work setups.

## Features

- Standard ARTSEY left-hand and right-hand layouts
- `2 fingers` on the trackpad: ARTSEY mode
- `3 fingers` on the trackpad: NAV mode
- Manual toggle
  - Left: `z + x + c + v`
  - Right: `m + , + . + /`
- NAV, mouse, media, bracket, and custom symbol layers
- `Esc` clears ARTSEY lock state

## Keyboard

- Designed primarily for MacBook built-in keyboards and standard Mac ANSI layouts.
- The left-hand block uses `qwer / asdf`.
- The right-hand block uses `uiop / jkl;`.
- Best experience on a MacBook trackpad.
- Still usable with external keyboards and manual toggles, even without multitouch.

### Base Layout

```text
Left hand

physical:  q  w  e  r
           a  s  d  f

output:    s  t  r  a
           o  i  y  e


Right hand

physical:  u  i  o  p
           j  k  l  ;

output:    a  r  t  s
           e  y  i  o
```

## Compatibility

- Recommended: `Karabiner-Elements 15.x`
- Recommended: `macOS 13+`
- Multitouch features require `Karabiner-MultitouchExtension` to be enabled in Karabiner Settings > Misc.
- Manual toggles still work even without multitouch.

## Install

1. Copy `artsey_complex_modifications.json` to:

```text
~/.config/karabiner/assets/complex_modifications/
```

2. Open Karabiner-Elements.
3. Go to `Complex Modifications`.
4. Click `Add predefined rule`.
5. Enable:
   - `ARTSEY Left (manual toggle: zxcv)`
   - `ARTSEY Right (manual toggle: m,./)`

## Usage

- Enable only the side you want to use, or enable both.
- `2 fingers = ARTSEY`
- `3 fingers = NAV`
- `Esc` clears ARTSEY lock state.

## Notes

- Tested primarily on a MacBook built-in keyboard.
- Multitouch activation requires the Karabiner Multitouch Extension.
- Some multi-key chords may feel different depending on keyboard rollover characteristics.

## Development

- `generate_karabiner_config.py`: generator for the Karabiner rule asset

The generator writes asset-only output:

```bash
python3 generate_karabiner_config.py
```

To also install the generated asset into your local Karabiner config:

```bash
python3 generate_karabiner_config.py --install
```

## License

MIT
