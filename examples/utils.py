def get_pan(patch, pan_position):
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


def get_sequence(patch, bpm, values):
    subp = patch.subpatch('seq')
    inbang = subp.obj('inlet')
    metro = subp.obj('metro', bpm)
    inbang[0].to(metro[0])

    i = subp.obj('i')
    metro[0].to(i[0])
    increment = subp.obj('+', 1)
    i[0].to(increment[0])
    
    mod = subp.obj('%', len(values))
    mod[0].to(i[1])
    increment[0].to(mod[0])

    indexes = [j for j in range(len(values))]
    selector = subp.obj('sel', *indexes)
    i[0].to(selector[0])

    out = subp.obj('outlet')
    for j, val in enumerate(values):
        msg = subp.msg(val)
        selector[j].to(msg[0])
        msg[0].to(out[0])

    return subp


def get_portamento(patch, portamento_ms):
    subp = patch.subpatch('portamento')
    line = subp.obj('line', 0, min(portamento_ms / 3, 20))
    inlet = subp.obj('inlet')
    outlet = subp.obj('outlet')
    pack = subp.obj('pack', 0, portamento_ms)
    inlet[0].to(pack[0])
    pack[0].to(line[0])
    line[0].to(outlet[0])

    return subp
