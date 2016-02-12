#!/usr/bin/env python3

from pdgen import PdPatch, render

patch = PdPatch()

sine = patch.obj('osc~', 332)
dac = patch.obj('dac~')
mult = patch.obj('*~', 0.05)

sine[0].to(mult[0])
mult[0].to(dac[0])
mult[0].to(dac[1])

print(render(patch))
