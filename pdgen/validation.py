import sys
import os

from . import PdType

CONTROL_PORT = 1
SIGNAL_PORT = 2

_flags = sys.getdlopenflags()
try:
    # PD externals refer to symbols from the python libpd extension, which by 
    # default aren't shared. This makes externals work. Probably not portable.
    sys.setdlopenflags(os.RTLD_NOW | os.RTLD_GLOBAL)
    import pylibpd
finally:
    sys.setdlopenflags(_flags)

OBJECT_ERROR = -1


def validate_obj(name, *args):
    obj_command = _make_cmd_string(name, args)

    if _is_special_obj(name):
        is_valid = _is_valid_special_obj(name, *args)
    else:
        is_valid = pylibpd.libpd_make_obj(obj_command) != OBJECT_ERROR

    if not is_valid:
        raise Exception("Invalid object %s" % (obj_command,))


def _get_outlet_type_for_subpatch(subpatch, index):
    outlets = subpatch.subpatch.get_sorted_outlets()
    if index >= len(outlets):
        return -1
    obj = outlets[index]
    return SIGNAL_PORT if obj.name == 'outlet~' else CONTROL_PORT


def _get_inlet_type_for_subpatch(subpatch, index):
    inlets = subpatch.subpatch.get_sorted_inlets()
    if index >= len(inlets):
        return -1
    obj = inlets[index]
    return SIGNAL_PORT if obj.name == 'inlet~' else CONTROL_PORT
    

def validate_connection(outlet, inlet):
    if outlet.parent.get_type() == PdType.OBJECT:
        if _is_special_obj(outlet.parent.name):
            outlet_type = _get_outlet_type_for_special_obj(outlet.parent, outlet.index)
        else:
            leaving_obj = _make_cmd_string(outlet.parent.name, outlet.parent.args)
            outlet_type = pylibpd.libpd_outlet_type(leaving_obj, outlet.index)
    elif outlet.parent.get_type() == PdType.SUBPATCH:
        outlet_type = _get_outlet_type_for_subpatch(outlet.parent, outlet.index)
    else:
        # All other elements have a single control input
        outlet_type = CONTROL_PORT if outlet.index == 0 else -1

    if outlet_type == -1:
        raise Exception("No outlet with index %u or object couldn't be created" %
                        (outlet.index,))

    if inlet.parent.get_type() == PdType.OBJECT:
        if _is_special_obj(inlet.parent.name):
            inlet_type = _get_inlet_type_for_special_obj(inlet.parent, inlet.index)
        else:
            entering_obj = _make_cmd_string(inlet.parent.name, inlet.parent.args)
            inlet_type = pylibpd.libpd_inlet_type(entering_obj, inlet.index)
    elif inlet.parent.get_type() == PdType.SUBPATCH:
        inlet_type = _get_inlet_type_for_subpatch(inlet.parent, inlet.index)
    else:
        inlet_type = CONTROL_PORT if inlet.index == 0 else -1

    if inlet_type == -1:
        raise Exception("No inlet with index %u or object couldn't be created" %
                        (inlet.index,))

    # Signal ports can accept control data but not the other way around
    if inlet_type == CONTROL_PORT and outlet_type == SIGNAL_PORT:
        raise Exception("Can't connect signal outlet to control inlet")


def add_externals_path(path):
    pylibpd.libpd_add_to_search_path(path)


def _make_cmd_string(name, args):
    cmd_list = [name]
    cmd_list.extend(args)
    obj_command = ' '.join(str(c) for c in cmd_list)
    return obj_command


# These cause segfaults if we try to create them with our hacked make_obj libpd function
def _is_special_obj(name):
    return name == 'inlet~' or name == 'outlet~' or \
        name == 'inlet' or name == 'outlet'


def _is_valid_special_obj(cmd_string, *args):
    # True for all special objs we know far
    return len(args) == 0


# Don't get confused here. inlet objects have outlets and outlet objects have inlets
def _get_inlet_type_for_special_obj(obj, inlet_index):
    if obj.name == 'outlet~':
        return SIGNAL_PORT if inlet_index == 0 else -1
    elif obj.name == 'outlet' and inlet_index == 0:
        return CONTROL_PORT if inlet_index == 0 else -1
    else:
        return -1


def _get_outlet_type_for_special_obj(obj, outlet_index):
    if obj.name == 'inlet~':
        return SIGNAL_PORT if outlet_index == 0 else -1
    elif obj.name == 'inlet' and outlet_index == 0:
        return CONTROL_PORT if outlet_index == 0 else -1
    else:
        return -1
