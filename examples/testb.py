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

def get_modulator(global_index, voice_index, total_voices, carrier_freq, freq_spread, width):
    subp = patch.subpatch('modulator')

    if global_index % 3 == 1:
        factor = 1200
    else:
        factor = 300

    if total_voices == 1:
        actual_carrier = carrier_freq
    else:
        low_freq = carrier_freq / freq_spread
        high_freq = carrier_freq * freq_spread
        actual_carrier = low_freq + \
                         voice_index * \
                         (high_freq - low_freq) / (total_voices - 1)
        

    env_length = (1000 / carrier_freq) * factor
    
    loadbang = subp.obj('loadbang')
    metro = subp.obj('metro', env_length)
    loadbang[0].to(metro[0])

    env_floor = 0.18

    def env_value(value):
        return (1.0 - env_floor) * value
    
    msg = subp.msg(env_value(1.0), env_length * 0.05, ",",
                   env_value(0.8), env_length * 0.25, env_length * 0.25, ",",
                   env_value(0), env_length * 0.3, env_length * 0.15)
    metro[0].to(msg[0])
    
    vline = subp.obj('vline~')
    msg[0].to(vline[0])

    floor = subp.obj('+~', env_floor)
    vline[0].to(floor[0])

    scaling = subp.obj('*~', width)
    floor[0].to(scaling[0])

    inlet = subp.obj('inlet~')
    env_mult = subp.obj('*~')
    inlet[0].to(env_mult[0])
    scaling[0].to(env_mult[1])
    
    add = subp.obj('+~', actual_carrier)
    env_mult[0].to(add[0])

    outlet = subp.obj('outlet~')
    add[0].to(outlet[0])

    return subp

dac = patch.obj('dac~')

#freqs = [(67, 1.0), (134, 0.8), (402, 0.8), (804, 0.2), (335 * 2, 0.35)]
# http://www.acoustics.asn.au/journal/1997/1997_25_3_McLachlan.pdf
#freqs = [(370 / 2, 1.0), (540 / 2, 0.8), (723 / 2, 0.8), (1080 / 2, 0.55), (1380 / 2, 0.65)]
freqs = []
#base_freq = 293
base_freq = 200
freqs.append((base_freq, 1.0))
freqs.append((base_freq * 7 / 4, 0.2))
freqs.append((base_freq * 19 / 9, 0.25))
oscs_per_freq = 4
oscs = len(freqs) * oscs_per_freq

low_cutoff = min(freq for freq, _ in freqs) * 0.8
hip_l = patch.obj('hip~', low_cutoff)
hip_r = patch.obj('hip~', low_cutoff)

i = 0
for carrier_freq, amplitude in freqs:
    for j in range(oscs_per_freq):
        modulator = get_modulator(i, j, oscs_per_freq, carrier_freq, 1.005, carrier_freq / 1.7)

        if i > 0:
            delread = patch.obj('delread~', 'fm_delay%u' % (i - 1,))
        else:
            delread = patch.obj('delread~', 'fm_delay%u' % (oscs - 1,))
        delread[0].to(modulator[0])

        sine = patch.obj('osc~')
        modulator[0].to(sine[0])

        if i % 3 == 0:
            delay_ms = (1000 / carrier_freq)
        else:
            delay_ms = (1000 / carrier_freq) * 20
            
        delwrite = patch.obj('delwrite~', 'fm_delay%u' % (i,), delay_ms)
        sine[0].to(delwrite[0])

        vol = 0.6 * amplitude
        mult = patch.obj('*~', vol / oscs)
        sine[0].to(mult[0])

        pan = get_pan((i * 300) % 80 - 40)
        mult[0].to(pan[0])

        pan[0].to(hip_l[0])
        pan[1].to(hip_r[0])

        i += 1

hip_l[0].to(dac[0])
hip_r[0].to(dac[1])

import sys
patch.accept(RenderVisitor(sys.stdout))

