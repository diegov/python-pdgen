#!/usr/bin/env python3

from pdgen import PdPatch, RenderVisitor, validation

import sys

if len(sys.argv) < 2:
    sys.stderr.write("Usage: test2.py path_to_freeverb\n")
    sys.exit(1)

freeverb_path = sys.argv[1]

validation.add_externals_path(freeverb_path)

patch = PdPatch(validate=True)

verb = patch.obj('freeverb~')
osc = patch.obj('osc~', 180)
dac = patch.obj('dac~')

osc[0].to(dac[0])
osc[0].to(dac[1])

import sys
patch.accept(RenderVisitor(sys.stdout))
