# Samba de Amigo: GameCube controller / Classic Controller input.
#
# The game calls KPADRead once per channel per frame (a single call site, in its
# input manager) into a 0x84-byte-per-sample KPADStatus buffer, then only ever
# looks at sample 0 -- the newest -- however many samples came back.  This hook
# replaces that `bl KPADRead`: it calls the real KPADRead, and when a GameCube
# pad answers on the matching SI port (or a Classic Controller is plugged into
# the Wii Remote) it rewrites sample 0 so the channel looks like a Wii Remote
# with a Nunchuk:
#
#   +0x00 hold  +0x04 trig  +0x08 release   Wii Remote buttons
#   +0x0C acc   (Vec)                       right hand  = the Wii Remote
#   +0x20 pos   (Vec2)                      IR pointer, driven by the left stick
#   +0x5C dev_type = 1 (Nunchuk)  +0x5E dpd_valid = 2
#   +0x68 acc   (Vec)                       left hand   = the Nunchuk
#   +0x18 / +0x74 acc_value                 length of each acc vector (the controller setup
#                                           averages it to spot the shake that picks a hand)
#
# Each hand's "acceleration" is one of five resting orientations (high, middle,
# low, left, right) picked from that hand's stick, plus a one-frame spike along
# the same direction when its shoulder button goes down: the game decides a
# shake from the jerk between frames and the circle from the direction a few
# frames later, so the orientation has to stay put while the spike goes by.
#
# Registers: r31 channel, r30 buffer, r29 sample count, r28 channel state,
#            r27 CFG, r26 source (1 = GC pad, 2 = Classic Controller)
# State:     0x2C we hold the connection bits  0x30 quiet frames
# Stack:     0x08 hold  0x0C lx  0x10 ly  0x14 rx  0x18 ry  0x1C shake L
#            0x20 shake R  0x28 scratch double
    stwu    1, -0x70(1)
    mflr    0
    stw     0, 0x74(1)
    stmw    24, 0x50(1)
    mr      31, 3
    mr      30, 4
    bl      KPADREAD
    mr      29, 3

    lis     27, CFG@h
    ori     27, 27, CFG@l
    lis     28, STATE@h
    ori     28, 28, STATE@l
    slwi    0, 31, 6
    add     28, 28, 0

    # first use: clear this channel's state
    lwz     0, 0(28)
    lis     4, MAGIC@h
    ori     4, 4, MAGIC@l
    cmpw    0, 4
    beq     2f
    li      0, 0
    li      5, 16
    mtctr   5
    addi    6, 28, -4
1:  stwu    0, 4(6)
    bdnz    1b
    stw     4, 0(28)
2:
    # ---- who is driving this channel? ----
    li      26, 0
    lwz     0, FLAGS(27)
    andi.   0, 0, 1
    beq     4f                          # GameCube pads disabled
    cmplwi  31, 2
    bge     4f
    lis     4, 0xCD00
    mulli   0, 31, 12
    add     4, 4, 0
    lwz     5, 0x6404(4)                # SIC0INBUFH: buttons, main stick
    lwz     6, 0x6408(4)                # SIC0INBUFL: C stick, triggers
    stw     5, 0x20(28)                 # (kept for debugging)
    stw     6, 0x24(28)
    rlwinm. 0, 5, 0, 0, 0               # error bit
    bne     4f
    rlwinm. 0, 5, 0, 8, 8               # bit 23 is always set in a pad's answer
    beq     4f
    li      26, 1
    b       5f
4:  lwz     0, FLAGS(27)
    andi.   0, 0, 2
    beq     Ldone                       # Classic Controller disabled
    lbz     0, 0x5C(30)                 # dev_type
    cmplwi  0, 2
    bne     Ldone
    li      26, 2
5:
    # ---- connection bookkeeping ----
    # The game decides which hands exist from its own flags, set by the WPAD connect and
    # extension callbacks, which never fire for a pad: a byte of "Wii Remote on channel c"
    # (bit 2c) / "Nunchuk on channel c" (bit 2c+1) bits, the same bits again in the byte
    # below it, and a per-channel connected word.  Without them the controller setup
    # sees nobody and asks for a Nunchuk.  Set them here while the pad drives the channel.
    lwz     12, CONNOFF(27)
    add     12, 12, 13
    slwi    10, 31, 1
    li      11, 3
    slw     11, 11, 10
    lbz     0, 0(12)
    or      0, 0, 11
    stb     0, 0(12)
    li      11, 1
    slw     11, 11, 10
    lbz     0, -1(12)
    or      0, 0, 11
    stb     0, -1(12)
    lwz     12, CONNST(27)
    mulli   10, 31, 20
    li      0, 1
    stwx    0, 12, 10
    stw     0, 0x2C(28)                 # we hold this channel's bits
    li      0, 0
    stw     0, 0x30(28)                 # frames since the pad went quiet
    # ---- gather: hold bits, two sticks (percent), two shake buttons ----
    cmpwi   26, 2
    beq     6f
    # GameCube pad: r5 = INBUFH, r6 = INBUFL
    rlwinm  7, 5, 24, 24, 31
    addi    7, 7, -128
    stw     7, 0x0C(1)                  # lx
    rlwinm  7, 5, 0, 24, 31
    addi    7, 7, -128
    stw     7, 0x10(1)                  # ly
    rlwinm  7, 6, 8, 24, 31
    addi    7, 7, -128
    stw     7, 0x14(1)                  # rx
    rlwinm  7, 6, 16, 24, 31
    addi    7, 7, -128
    stw     7, 0x18(1)                  # ry
    rlwinm  7, 5, 10, 31, 31
    stw     7, 0x1C(1)                  # L -> left shake
    rlwinm  7, 5, 11, 31, 31
    stw     7, 0x20(1)                  # R -> right shake
    mr      9, 5
    addi    8, 27, GCMAP
    b       7f
6:  # Classic Controller: ex_status.cl at +0x60
    lwz     9, 0x60(30)                 # hold
    lfs     1, SCALE(27)
    lfs     0, 0x6C(30)
    fmuls   0, 0, 1
    fctiwz  0, 0
    stfd    0, 0x28(1)
    lwz     7, 0x2C(1)
    stw     7, 0x0C(1)
    lfs     0, 0x70(30)
    fmuls   0, 0, 1
    fctiwz  0, 0
    stfd    0, 0x28(1)
    lwz     7, 0x2C(1)
    stw     7, 0x10(1)
    lfs     0, 0x74(30)
    fmuls   0, 0, 1
    fctiwz  0, 0
    stfd    0, 0x28(1)
    lwz     7, 0x2C(1)
    stw     7, 0x14(1)
    lfs     0, 0x78(30)
    fmuls   0, 0, 1
    fctiwz  0, 0
    stfd    0, 0x28(1)
    lwz     7, 0x2C(1)
    stw     7, 0x18(1)
    li      7, 0
    andi.   0, 9, 0x2080                # ZL / L
    beq     1f
    li      7, 1
1:  stw     7, 0x1C(1)
    li      7, 0
    andi.   0, 9, 0x0204                # ZR / R
    beq     1f
    li      7, 1
1:  stw     7, 0x20(1)
    addi    8, 27, CCMAP
7:  # map source buttons -> Wii Remote bits (table of mask pairs, 0-terminated)
    li      10, 0
1:  lwz     0, 0(8)
    cmpwi   0, 0
    beq     3f
    and.    4, 9, 0
    beq     2f
    lwz     4, 4(8)
    or      10, 10, 4
2:  addi    8, 8, 8
    b       1b
3:  # the real remote's own buttons still count (fresh samples only)
    cmpwi   29, 0
    ble     1f
    lwz     0, 0(30)
    or      10, 10, 0
1:  stw     10, 0x08(1)

    # ---- pointer: the left stick moves it, in thousandths of the screen ----
    lwz     11, DEADZONE(27)
    lwz     12, SPEED(27)
    lwz     7, 0x0C(1)                  # lx
    srawi   0, 7, 31
    xor     4, 7, 0
    subf    4, 0, 4
    cmpw    4, 11
    blt     1f
    mullw   7, 7, 12
    srawi   7, 7, 7
    lwz     4, 0x08(28)
    add     4, 4, 7
    cmpwi   4, 1000
    ble     2f
    li      4, 1000
2:  cmpwi   4, -1000
    bge     3f
    li      4, -1000
3:  stw     4, 0x08(28)
1:  lwz     7, 0x10(1)                  # ly (up is positive, the pointer's y is down-positive)
    srawi   0, 7, 31
    xor     4, 7, 0
    subf    4, 0, 4
    cmpw    4, 11
    blt     1f
    mullw   7, 7, 12
    srawi   7, 7, 7
    lwz     4, 0x0C(28)
    subf    4, 7, 4
    cmpwi   4, 1000
    ble     2f
    li      4, 1000
2:  cmpwi   4, -1000
    bge     3f
    li      4, -1000
3:  stw     4, 0x0C(28)
1:

    # ---- hands: class (0 high, 1 middle, 2 low, 3 left, 4 right) per stick ----
.macro CLASS sx, sy, out
    lwz     4, \sx(1)
    lwz     5, \sy(1)
    srawi   0, 4, 31
    xor     6, 4, 0
    subf    6, 0, 6                     # |sx|
    srawi   0, 5, 31
    xor     7, 5, 0
    subf    7, 0, 7                     # |sy|
    li      \out, 1
    lwz     0, THRESH(27)
    cmpw    6, 0
    bgt     1f
    cmpw    7, 0
    ble     9f
1:  cmpw    7, 6
    blt     2f
    cmpwi   5, 0
    li      \out, 0
    bgt     9f
    li      \out, 2
    b       9f
2:  cmpwi   4, 0
    li      \out, 4
    bgt     9f
    li      \out, 3
9:
.endm

    # left hand (the Nunchuk) -> r14-ish via stack; right hand (the remote)
    CLASS   0x0C, 0x10, 9               # r9  = left class
    CLASS   0x14, 0x18, 10              # r10 = right class

    # shake edges (state +0x10 / +0x14 = pending spike, +0x18 / +0x1C = previous button)
    lwz     4, 0x1C(1)
    lwz     5, 0x18(28)
    stw     4, 0x18(28)
    andc    4, 4, 5
    cmpwi   4, 0
    beq     1f
    li      0, 1
    stw     0, 0x10(28)
1:  lwz     4, 0x20(1)
    lwz     5, 0x1C(28)
    stw     4, 0x1C(28)
    andc    4, 4, 5
    cmpwi   4, 0
    beq     1f
    li      0, 1
    stw     0, 0x14(28)
1:
    # left vector -> f1..f3 ; right vector -> f4..f6
    mulli   4, 9, 12
    add     4, 4, 27
    lfs     1, 0(4)
    lfs     2, 4(4)
    lfs     3, 8(4)
    mulli   4, 10, 12
    add     4, 4, 27
    lfs     4, 0(4)
    lfs     5, 4(4)
    lfs     6, 8(4)
    lfs     0, SPIKE(27)
    lfs     11, ONE(27)                 # acc_value (the vector's length): 1 at rest ...
    fmr     12, 11
    lwz     4, 0x10(28)
    cmpwi   4, 0
    beq     1f
    fmuls   1, 1, 0
    fmuls   2, 2, 0
    fmuls   3, 3, 0
    fmr     11, 0                       # ... the spike on the frame the button goes down
    li      4, 0
    stw     4, 0x10(28)
1:  lwz     4, 0x14(28)
    cmpwi   4, 0
    beq     1f
    fmuls   4, 4, 0
    fmuls   5, 5, 0
    fmuls   6, 6, 0
    fmr     12, 0
    li      4, 0
    stw     4, 0x14(28)
1:
    # pointer ints -> floats
    lfd     7, MAGIC_D(27)
    lis     0, 0x4330
    stw     0, 0x28(1)
    lfs     8, INV1000(27)
    lwz     4, 0x08(28)
    xoris   4, 4, 0x8000
    stw     4, 0x2C(1)
    lfd     9, 0x28(1)
    fsub    9, 9, 7
    frsp    9, 9
    fmuls   9, 9, 8                     # pointer x
    lwz     4, 0x0C(28)
    xoris   4, 4, 0x8000
    stw     4, 0x2C(1)
    lfd     10, 0x28(1)
    fsub    10, 10, 7
    frsp    10, 10
    fmuls   10, 10, 8                   # pointer y

    # ---- write sample 0 ----
    lwz     4, 0x08(1)                  # hold
    lwz     5, 0x04(28)                 # previous hold
    stw     4, 0x04(28)
    andc    6, 4, 5
    andc    7, 5, 4
    stw     4, 0x00(30)
    stw     6, 0x04(30)
    stw     7, 0x08(30)
    stfs    4, 0x0C(30)
    stfs    5, 0x10(30)
    stfs    6, 0x14(30)
    stfs    9, 0x20(30)
    stfs    10, 0x24(30)
    stfs    1, 0x68(30)
    stfs    2, 0x6C(30)
    stfs    3, 0x70(30)
    stfs    12, 0x18(30)                # acc_value, which the controller setup reads to catch a shake
    stfs    11, 0x74(30)                # (Nunchuk)
    li      0, 0
    stw     0, 0x1C(30)
    stw     0, 0x60(30)
    stw     0, 0x64(30)
    stw     0, 0x78(30)
    li      0, 1
    stb     0, 0x5C(30)                 # a Nunchuk is plugged in
    li      0, 0
    stb     0, 0x5D(30)
    li      0, 2
    stb     0, 0x5E(30)                 # pointer is valid
    lwz     4, 0x28(28)
    addi    4, 4, 1
    stw     4, 0x28(28)                 # frame counter (debugging)
    li      29, 1
    b       9f                          # driven this frame: keep the connection bits
Ldone:
    # nobody drives the channel: give the connection bits back (after 1.5 s of quiet, and
    # never if a real Wii Remote is sending samples -- it owns them then)
    lwz     0, 0x2C(28)
    cmpwi   0, 0
    beq     9f
    cmpwi   29, 0
    bgt     8f
    lwz     4, 0x30(28)
    addi    4, 4, 1
    stw     4, 0x30(28)
    cmpwi   4, 90
    blt     9f
    lwz     12, CONNOFF(27)
    add     12, 12, 13
    slwi    10, 31, 1
    li      11, 3
    slw     11, 11, 10
    lbz     0, 0(12)
    andc    0, 0, 11
    stb     0, 0(12)
    li      11, 1
    slw     11, 11, 10
    lbz     0, -1(12)
    andc    0, 0, 11
    stb     0, -1(12)
    lwz     12, CONNST(27)
    mulli   10, 31, 20
    li      0, 0
    stwx    0, 12, 10
8:  li      0, 0
    stw     0, 0x2C(28)
    stw     0, 0x30(28)
9:  mr      3, 29
    lmw     24, 0x50(1)
    lwz     0, 0x74(1)
    mtlr    0
    addi    1, 1, 0x70
    blr
