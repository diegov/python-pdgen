#!/usr/bin/env python3

from pdgen import PdPatch, RenderVisitor

patch = PdPatch()

osc = patch.obj('osc~', 180)
dac = patch.obj('dac~')

osc[0].to(dac[0])
osc[0].to(dac[1])

import sys
patch.accept(RenderVisitor(sys.stdout))
