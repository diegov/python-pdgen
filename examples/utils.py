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
