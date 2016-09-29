#!/usr/bin/env python3

from pdgen import PdPatch
from pdgen.project import PdFile

f = PdFile('abstr1.pd', patch=PdPatch(validate=True))
inlet = f.patch.obj('inlet~')
outlet = f.patch.obj('outlet~')

mul = f.patch.obj('*~')
inlet[0].to(mul[1])

osc = f.patch.obj('osc~', 311)
osc[0].to(mul[0])

mul[0].to(outlet[0])

f.save()

f2 = PdFile('main.pd', patch=PdPatch(validate=True))

dac = f2.patch.obj('dac~')

for i in range(4):
    main_osc = f2.patch.obj('osc~', 200 * (i + 1))
    abstr = f2.patch.abstr(f)
    main_osc[0].to(abstr[0])
    if i % 2 == 0:
        abstr[0].to(dac[0])
    else:
        abstr[0].to(dac[1])
        
f2.save()
