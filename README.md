# Samba Patch

Play the Wii release of **Samba de Amigo** with a **GameCube controller** or a
**Classic Controller**. Works with the USA (`R3BE8P`), European (`R3BP8P`) and
Japanese (`R3BJ8P`) releases. The patch is applied to your own copy of the game;
nothing from the game is in this repository.

## How it plays

The game reads the Wii Remote (right maraca) and Nunchuk (left maraca). The patch
makes a pad look like both:

| Input | Action |
| --- | --- |
| Left stick | Left maraca position (high / middle / low / left / right; a diagonal reaches the sixth pose, e.g. the top-left calibration ring) |
| C stick (GameCube) / right stick (Classic) | Right maraca position (same, diagonals included) |
| L / ZL | Shake the left maraca |
| R / ZR | Shake the right maraca |
| Left stick (menus) | Move the pointer |
| A, B, X (1), Y (2), Start (+), D-pad | Wii Remote buttons |

The game's controller setup ("shake the Wii Remote and the Nunchuk") works with the
pad too: press L, then R, where it asks for a shake. The patch also fills in the
game's own "Wii Remote and Nunchuk connected" flags, which only the Wii Remote
connect callbacks set, so no real Wii Remote or Nunchuk is needed to get past the
"Connect a Nunchuk" screen.

A GameCube pad in port 1 / 2 drives Wii Remote 1 / 2. A Classic Controller works
when plugged into the Wii Remote. A real Wii Remote still works next to the pad.

## Use

**GUI (recommended):** run the Samba Patcher app, tick the controllers you want,
and drop a `.wbfs` or `.iso` on the window. The disc is patched in place (so USB
loaders still find it) and the original is kept next to it as `<name>.bak`.
Builds for macOS, Linux and Windows come from the *Build GUI patcher* workflow.

**Command line:**

```bash
python3 tools/gui.py                                                                 # the GUI from source
python3 tools/sambapatch.py disc "Samba de Amigo (USA) (En,Fr,Es).rvz" patched.iso   # output .iso or .wbfs
python3 tools/sambapatch.py dol main.dol main_patched.dol                            # just the DOL
python3 tools/sambapatch.py riivolution                                              # riivolution/ for an SD card
```

Disc patching needs [wit](https://wit.wiimm.de/) (bundled in the GUI builds). The
Gecko cheat route is not offered: the hook lives at `0x80001820`, where USB
loaders keep their code handler.

## Building

End users need no toolchain: the assembled hook ships in `tools/prebuilt/pads.json`.
After editing `src/pads.s`, with [devkitPPC](https://devkitpro.org/) installed:

```bash
python3 tools/gen_prebuilt.py          # rebuild pads.json  (--check to verify it is current)
python3 tools/sambapatch.py riivolution
python3 -m PyInstaller --name Samba-Patcher --windowed --collect-all tkinterdnd2 \
  --icon assets/icon.icns --paths tools --paths src --add-data assets/logo.png:assets \
  --add-data tools/prebuilt:tools/prebuilt --add-binary "$(which wit):." tools/gui.py
```

## Layout

- `src/pads.s`, `src/gen_pads.py` the hook (replaces the one `bl KPADRead` in the input manager)
- `tools/` DOL editor, region table, patcher (`sambapatch.py`), GUI (`gui.py`), prebuilt hook, assembler wrapper
- `lab/` throwaway Dolphin harness (GDB stub + input pipes) used to test
- `tests/test_patch.py` patches all three DOLs and checks the result

Boot-tested in Dolphin on all three releases (GC pad: A, stick pointer, hook running each frame).
