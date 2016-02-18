#!/usr/bin/env python3

import sys
sys.path.append('../..')
sys.path.append('../libpd/python/build/lib.linux-x86_64-3.5')

from pdgen import PdPatch, RenderVisitor
from pdgen.audition import audition
from utils import get_pan

patch = PdPatch()

def get_modulator(carrier_freq, modulator_freq, width):
    subp = patch.subpatch('modulator')

    env_length = (1000 / carrier_freq) * 35
    
    metro = subp.obj('metro', env_length)
    # Make sure it gets started with the patch
    subp.loadbang(metro[0])
    
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

    pan = get_pan(patch, (i * 300) % 80 - 40)
    mult[0].to(pan[0])
    
    pan[0].to(freeverb[0])
    pan[1].to(freeverb[1])

    pan[0].to(dac[0])
    pan[1].to(dac[1])

    carrier_freq *= 1.0005
    mod_freq *= 1.19

import sys
patch.accept(RenderVisitor(sys.stdout))

audition(patch)
