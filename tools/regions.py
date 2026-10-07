"""Per-release addresses.

The USA main.dol was read in Ghidra: the game's input manager calls KPADRead once
per channel per frame from a single place.  The other two releases were found by
matching the surrounding code (branch targets and immediates masked, tools/sig.py)
against the USA DOL; each match was unique.
"""


class Region:
    def __init__(self, disc_id, name, site, kpad_read):
        self.disc_id, self.name = disc_id, name
        self.site = site                # the `bl KPADRead` in the input manager
        self.kpad_read = kpad_read

    def __repr__(self):
        return '%s (%s)' % (self.name, self.disc_id)


REGIONS = {
    'R3BE8P': Region('R3BE8P', 'USA', 0x80116DAC, 0x802F5948),
    'R3BP8P': Region('R3BP8P', 'Europe', 0x80116DA8, 0x802F5948),
    'R3BJ8P': Region('R3BJ8P', 'Japan', 0x80117620, 0x802F6D28),
}
