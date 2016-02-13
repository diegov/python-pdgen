#!/usr/bin/env python3

from pdgen import PdPatch, RenderVisitor

patch = PdPatch()

def get_pan(pan_position):
    subp = patch.subpatch('pan')

    loadbang = subp.obj('loadbang')
    msg = subp.msg(pan_position)
    loadbang[0].to(msg[0])

    inlet = subp.obj('inlet~')
    
    pan = subp.obj('pan~')
    msg[0].to(pan[1])
    inlet[0].to(pan[0])

    # TODO: Force position!
    outletl = subp.obj('outlet~')
    outletr = subp.obj('outlet~')

    pan[0].to(outletl[0])
    pan[1].to(outletr[0])

    return subp

def get_modulator(carrier_freq, modulator_freq, width):
    subp = patch.subpatch('modulator')

    env_length = (1000 / carrier_freq) * 35
    
    loadbang = subp.obj('loadbang')
    metro = subp.obj('metro', env_length)
    loadbang[0].to(metro[0])
    
    msg = subp.msg(1.0, env_length * 0.05, ",",
                   0.8, env_length * 0.25, env_length * 0.25, ",",
                   0, env_length * 0.3, env_length * 0.15)
    metro[0].to(msg[0])
    
    vline = subp.obj('vline~')
    msg[0].to(vline[0])
    
    inlet = subp.obj('inlet~')
    env_mult = subp.obj('*~')
    inlet[0].to(env_mult[0])
    vline[0].to(env_mult[1])
    
    modulator = subp.obj('osc~', modulator_freq)
    
    mult = subp.obj('*~', width)
    vline[0].to(mult[0])
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

#carrier_freq = 220
#mod_freq = 400

carrier_freq = 220
mod_freq = 333

oscs = 12
for i in range(oscs):
    #modulator = get_modulator(carrier_freq, mod_freq, carrier_freq / 3.0)
    modulator = get_modulator(carrier_freq, carrier_freq * 3, carrier_freq * 2.1)

    if i > 0:
        delread = patch.obj('delread~', 'fm_delay%u' % (i - 1,))
        delread[0].to(modulator[0])

    sine = patch.obj('osc~')
    modulator[0].to(sine[0])

    delwrite = patch.obj('delwrite~', 'fm_delay%u' % (i,), carrier_freq)
    sine[0].to(delwrite[0])

    mult = patch.obj('*~', 0.3 / oscs)
    sine[0].to(mult[0])

    pan = get_pan((i * 300) % 80 - 40)
    mult[0].to(pan[0])
    
    pan[0].to(freeverb[0])
    pan[1].to(freeverb[1])

    pan[0].to(dac[0])
    pan[1].to(dac[1])

    carrier_freq *= 1.0005
    mod_freq *= 1.19

import sys
patch.accept(RenderVisitor(sys.stdout))

