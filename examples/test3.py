import sys
sys.path.append('../..')

from pdgen import PdPatch, RenderVisitor
from utils import get_sequence, get_portamento

import math

patch = PdPatch()

dac = patch.obj('dac~')

freqs = [200, 210, 250, 289, 295]

min_freq = min(freqs)

hip = patch.obj('hip~', min_freq * 0.9)

base_ratios = [f / min_freq for f in freqs]
seq_ratios = [1.0, 1.025, 1.5, 1.08, 1.55, 1.125, 1.66, 1.33]

am_mod = None
for i, freq in enumerate(freqs):
    base_ratio = base_ratios[i]
    seq_freqs = [freq * ratio * base_ratio for ratio in seq_ratios]
    seq = get_sequence(patch, 120, seq_freqs)
    
    patch.loadbang(seq[0])
    osc = patch.obj('osc~')

    portamento = get_portamento(patch, 15 * (1000 / freq))
    
    seq[0].to(portamento[0])
    portamento[0].to(osc[0])

    mult = patch.obj('*~', 1.0 / math.sqrt(len(freqs)))

    osc[0].to(mult[0])

    new_am_mod = patch.obj('*~')
    if am_mod is not None:
        mult[0].to(am_mod[1])
        am_mod[0].to(new_am_mod[0])
    else:
        mult[0].to(new_am_mod[0])

    am_mod = new_am_mod

    am_mod[0].to(hip[0])

hip[0].to(dac[0])
hip[0].to(dac[1])

import sys
patch.accept(RenderVisitor(sys.stdout))

