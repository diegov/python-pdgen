#!/usr/bin/env python3

import sys
import networkx as nx
import os


def _import_validation():
    try:
        from . import validation
    except ImportError as e:
        sys.stderr.write('Validation requires the pylibpd package\n')
        raise e


class InletOutlet(object):
    def __init__(self, parent, index):
        self.parent = parent
        self.index = index

    def to(self, inlet):
        self.parent.outlet(self.index).to(inlet)

    def as_inlet(self):
        return self.parent.inlet(self.index)


class Inlet(object):
    def __init__(self, parent, index):
        self.parent = parent
        self.index = index


class Outlet(object):
    def __init__(self, parent, index, validate):
        self.parent = parent
        self.inlets = []
        self.index = index
        self.validate = validate
        if self.validate:
            _import_validation()

    def to(self, inlet):
        if isinstance(inlet, InletOutlet):
            inlet = inlet.as_inlet()

        edge_id = self.parent.patch.next_key()
        self.parent.patch.graph.add_edge(self.parent.id,
                                         inlet.parent.id, edge_id)
        if self.validate:
            validation.validate_connection(self, inlet)
        self.inlets.append((inlet, edge_id))


class PdType:
    ELEMENT = 1
    OBJECT = 2
    SUBPATCH = 3


class PdElement(object):
    def __init__(self, patch, id, validate, *args):
        self.patch = patch
        self.id = id
        self.validate = validate
        self.args = args
        self.ins = {}
        self.outlets = {}

    def inlet(self, index):
        if index not in self.ins:
            self.ins[index] = Inlet(self, index)
        return self.ins[index]

    def outlet(self, index):
        if index not in self.outlets:
            self.outlets[index] = Outlet(self, index, self.validate)
        return self.outlets[index]

    def get_type(self):
        return PdType.ELEMENT

    def __getitem__(self, index):
        return InletOutlet(self, index)

    def __repr__(self):
        fmt_string = '{0} id: {1} args: {2}'
        return fmt_string.format(type(self), self.id,
                                 ','.join([str(arg) for arg in self.args]))

                                                    
class PdObject(PdElement):
    def __init__(self, patch, id, name, validate, *args):
        super(PdObject, self).__init__(patch, id, validate, *args)
        self.name = name

    def accept(self, render_visitor, ctx=None):
        render_visitor.visit_pd_obj(self, ctx=ctx)

    def get_type(self):
        return PdType.OBJECT

    def __repr__(self):
        fmt_string = '{0} name: {1} args: {2}'
        return fmt_string.format(type(self), self.name,
                                 ','.join([str(arg) for arg in self.args]))



# TODO: These are useless at the moment
class PdInletObj(PdObject):
    def __init__(self, patch, id, is_signal, validate):
        name = 'inlet~' if is_signal else 'inlet'
        super(PdInletObj, self).__init__(patch, id, name, validate)

    def accept(self, render_visitor, ctx=None):
        render_visitor.visit_inlet_obj(self, ctx=ctx)


class PdOutletObj(PdObject):
    def __init__(self, patch, id, is_signal, validate):
        name = 'outlet~' if is_signal else 'outlet'
        super(PdOutletObj, self).__init__(patch, id, name, validate)

    def accept(self, render_visitor, ctx=None):
        render_visitor.visit_outlet_obj(self, ctx=ctx)


class PdMessage(PdElement):
    def __init__(self, patch, id, validate, *args):
        super(PdMessage, self).__init__(patch, id, validate, *args)

    def accept(self, render_visitor, ctx=None):
        render_visitor.visit_pd_msg(self, ctx=ctx)


class PdPatch(object):
    def __init__(self, validate=False):
        self.graph = nx.MultiDiGraph()
        self.objects = {}
        self.seq = 0
        self._loadbang = None
        self.validate = validate
        if self.validate:
            _import_validation()

        self.abstraction_files = []

    def next_key(self):
        self.seq += 1
        return self.seq

    def _add_element(self, factory):
        node_id = self.next_key()
        self.graph.add_node(node_id)
        newelement = factory(node_id)
        self.objects[node_id] = newelement
        return newelement

    # TODO: $ args
    def abstr(self, pd_file):
        if not pd_file in self.abstraction_files:
            self.abstraction_files.append(pd_file)
        name = os.path.splitext(pd_file.filepath)[0]
        return self.obj(name)

    def obj(self, name, *args):
        name = name.strip().lower()
        if self.validate:
            validation.validate_obj(name, *args)

        handled = self._handle_special_object(name, args)
        if handled is not None:
            return handled
        
        return self._add_element(lambda node_id: PdObject(self, node_id, name,
                                                          self.validate, *args))

    def subpatch(self, name):
        return self._add_element(lambda node_id: PdSubPatch(self, node_id,
                                                            name, self.validate))

    def msg(self, *args):
        return self._add_element(lambda node_id: PdMessage(self, node_id,
                                                           self.validate, *args))

    def loadbang(self, inlet):
        if self._loadbang is None:
            self._loadbang = self.obj('loadbang')
        self._loadbang[0].to(inlet)

    def inlet_obj(self, is_signal):
        return self._add_element(lambda node_id: PdInletObj(self, node_id,
                                                            is_signal, self.validate))

    def outlet_obj(self, is_signal):
        return self._add_element(lambda node_id: PdOutletObj(self, node_id,
                                                             is_signal, self.validate))

    def accept(self, render_visitor, ctx=None):
        render_visitor.visit_pd_patch(self, ctx=ctx)

    def get_sorted_inlets(self):
        return sorted([self.objects[k] for k in self.objects if isinstance(self.objects[k], PdInletObj)],
                        key=lambda x: x.id)

    def get_sorted_outlets(self):
        return sorted([self.objects[k] for k in self.objects if isinstance(self.objects[k], PdOutletObj)],
                        key=lambda x: x.id)
        
    def _handle_special_object(self, name, args):
        if name == 'inlet':
            return self.inlet_obj(False)
        elif name == 'inlet~':
            return self.inlet_obj(True)
        elif name == 'outlet':
            return self.outlet_obj(False)
        elif name == 'outlet~':
            return self.outlet_obj(True)

        return None


# TODO force layout of inlets and outlets to have stable order
class PdSubPatch(PdElement):
    def __init__(self, patch, id, name, validate):
        super(PdSubPatch, self).__init__(patch, id, validate)
        self.subpatch = PdPatch(validate=validate)
        self.name = name

    def accept(self, render_visitor, ctx=None):
        render_visitor.visit_pd_subpatch(self, ctx=ctx)

    def __getattr__(self, name):
        if not hasattr(self.subpatch, name):
            raise AttributeError('No attribute with name ' + name)
        return getattr(self.subpatch, name)

    def __repr__(self):
        fmt_string = 'PdSubPatch name: {0}'
        return fmt_string.format(self.name)

    def get_type(self):
        return PdType.SUBPATCH


class RenderVisitor(object):
    def __init__(self, out):
        self.out = out

    def render_arg(self, arg):
        return str(arg).replace(',', '\\,')

    def visit_pd_obj(self, pd_obj, ctx=None):
        args = ''
        for arg in pd_obj.args:
            args += ' ' + self.render_arg(arg)
        x_pos = ctx['x_pos']
        y_pos = ctx['y_pos']
        line = "#X obj %u %u %s%s;\n" % (x_pos, y_pos, pd_obj.name, args)
        self.out.write(line)

    def visit_inlet_obj(self, pd_obj, ctx=None):
        self.visit_pd_obj(pd_obj, ctx=ctx)

    def visit_outlet_obj(self, pd_obj, ctx=None):
        self.visit_pd_obj(pd_obj, ctx=ctx)

    def visit_pd_msg(self, pd_msg, ctx=None):
        args = ''
        for arg in pd_msg.args:
            args += ' ' + self.render_arg(arg)
        x_pos = ctx['x_pos']
        y_pos = ctx['y_pos']
        line = "#X msg %u %u%s;\n" % (x_pos, y_pos, args)
        self.out.write(line)

    def visit_pd_subpatch(self, pd_obj, ctx=None):
        new_ctx = {}
        new_ctx['subpatch'] = pd_obj.name
        new_ctx = dict(ctx, **new_ctx)
        self.visit_pd_patch(pd_obj.subpatch, new_ctx)
        x_pos = ctx['x_pos']
        y_pos = ctx['y_pos']
        line = "#X restore %u %u pd %s;\n" % (x_pos, y_pos, pd_obj.name)
        self.out.write(line)

    def visit_pd_patch(self, patch, ctx=None):
        if ctx is None:
            ctx = {}
        else:
            ctx = dict(ctx)

        height = 20 * len(patch.graph.nodes())
        width  = 20 * len(patch.graph.nodes())

        startline = '#N canvas 1 1 500 500 '
        if 'subpatch' in ctx:
            startline += ctx['subpatch'] + ' '
            
        startline += '10;\n'
        self.out.write(startline)
        
        out_indices = {}
        # TODO: graphviz layout
        positions = nx.spring_layout(patch.graph)
        try:
            sorted_nodes = nx.topological_sort(patch.graph)
        except nx.NetworkXUnfeasible:
            # If there's a cycle, we can't sort
            sorted_nodes = patch.graph.nodes()

        # HACK to ensure inlets and outlets are in the right order
        inlets = patch.get_sorted_inlets()
        
        outlets = patch.get_sorted_outlets()

        # More hacks
        forced_x_layouts = {obj.id: ndx / len(inlets) for ndx, obj in enumerate(inlets)}
        forced_x_layouts.update({obj.id: ndx / len(outlets) for ndx, obj in enumerate(outlets)})

        for key in forced_x_layouts:
            positions[key][0] = forced_x_layouts[key]

        for ndx, id in enumerate(sorted_nodes):
            pd_obj = patch.objects[id]
            out_indices[id] = ndx
            x_pos = int(positions[id][0] * width)
            y_pos = int(positions[id][1] * height)

            ctx = {}
            ctx['x_pos'] = x_pos
            ctx['y_pos'] = y_pos

            pd_obj.accept(self, ctx=ctx)

        for id in sorted_nodes:
            pd_obj = patch.objects[id]
            for out_ndx in sorted(pd_obj.outlets.keys()):
                outlet = pd_obj.outlets[out_ndx]
                for inlet, edge_id in outlet.inlets:
                    out_obj_ndx = out_indices[outlet.parent.id]
                    in_obj_ndx = out_indices[inlet.parent.id]
                    line = "#X connect %u %u %u %u;\n" % \
                           (out_obj_ndx, outlet.index, in_obj_ndx, inlet.index)
                    self.out.write(line)
