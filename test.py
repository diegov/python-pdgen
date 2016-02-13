#!/usr/bin/env python3

from pdgen import PdPatch, RenderVisitor

patch = PdPatch()

def get_modulator(carrier_freq, modulator_freq, width):
    subp = patch.subpatch('modulator')

    inlet = subp.obj('inlet~')
    modulator = subp.obj('osc~', modulator_freq)
    
    mult = subp.obj('*~', width)
    inlet[0].to(mult[0])
    modulator[0].to(mult[0])
    
    add = subp.obj('+~', carrier_freq)
    mult[0].to(add[0])

    outlet = subp.obj('outlet~')
    add[0].to(outlet[0])

    return subp

dac = patch.obj('dac~')
freeverb = patch.obj('freeverb~')
freeverb[0].to(dac[0])
freeverb[1].to(dac[1])

carrier_freq = 220
mod_freq = 400

oscs = 12
for i in range(oscs):
    #modulator = get_modulator(carrier_freq, mod_freq, carrier_freq / 3.0)
    modulator = get_modulator(carrier_freq, carrier_freq * 3, carrier_freq / 1.3)

    if i > 0:
        delread = patch.obj('delread~', 'fm_delay%u' % (i - 1,))
        delread[0].to(modulator[0])

    sine = patch.obj('osc~')
    modulator[0].to(sine[0])

    delwrite = patch.obj('delwrite~', 'fm_delay%u' % (i,), carrier_freq)
    sine[0].to(delwrite[0])

    mult = patch.obj('*~', 0.3 / oscs)
    sine[0].to(mult[0])
    
    mult[0].to(freeverb[0])
    mult[0].to(freeverb[1])

    mult[0].to(dac[0])
    mult[0].to(dac[1])

    carrier_freq *= 1.0005
    mod_freq *= 1.19

import sys
patch.accept(RenderVisitor(sys.stdout))

