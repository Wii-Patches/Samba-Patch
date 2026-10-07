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
| Left stick | Left maraca position (high / middle / low / left / right) |
| C stick (GameCube) / right stick (Classic) | Right maraca position |
| L / ZL | Shake the left maraca |
| R / ZR | Shake the right maraca |
| Left stick (menus) | Move the pointer |
| A, B, X (1), Y (2), Start (+), D-pad | Wii Remote buttons |

A GameCube pad in port 1 / 2 drives Wii Remote 1 / 2. A Classic Controller works
when plugged into the Wii Remote. A real Wii Remote still works next to the pad.

## Use

```bash
python3 tools/sambapatch.py disc "Samba de Amigo (USA) (En,Fr,Es).rvz" patched.iso   # also .wbfs / .rvz
python3 tools/sambapatch.py dol main.dol main_patched.dol                            # just the DOL
python3 tools/sambapatch.py riivolution                                              # riivolution/ for an SD card
```

Disc patching needs [wit](https://wit.wiimm.de/). The Gecko cheat route is not
offered: the hook lives at `0x80001820`, where USB loaders keep their code handler.

## Layout

- `src/pads.s`, `src/gen_pads.py` the hook (replaces the one `bl KPADRead` in the input manager)
- `tools/` DOL editor, assembler wrapper (devkitPPC), region table, patcher
- `lab/` throwaway Dolphin harness (GDB stub + input pipes) used to test
- `tests/test_patch.py` patches all three DOLs and checks the result

Tested in Dolphin on the USA release. Europe and Japan sites were found by
signature match against the USA DOL (unique) and are not yet boot-tested.
