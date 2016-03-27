import sys
import os

_flags = sys.getdlopenflags()
# PD externals refer to symbols from the python libpd extension, which by 
# default aren't shared. This makes externals work. Probably not portable.
sys.setdlopenflags(os.RTLD_NOW | os.RTLD_GLOBAL)
import pylibpd
sys.setdlopenflags(_flags)

OBJECT_ERROR = -1

def validate_obj(name, *args):
    cmd_list = [name]
    cmd_list.extend(args)
    obj_command = ' '.join(str(c) for c in cmd_list)
    if pylibpd.libpd_make_obj(obj_command) == OBJECT_ERROR:
        raise Exception("Invalid object %s" % (obj_command,))


def validate_connection(outlet, inlet):
    # TODO
    pass


def add_externals_path(path):
    pylibpd.libpd_add_to_search_path(path)
