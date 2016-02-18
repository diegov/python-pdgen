#!/usr/bin/env python3

import networkx as nx

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
    def __init__(self, parent, index):
        self.parent = parent
        self.inlets = []
        self.index = index

    def to(self, inlet):
        if isinstance(inlet, InletOutlet):
            inlet = inlet.as_inlet()

        edge_id = self.parent.patch.next_key()
        self.parent.patch.graph.add_edge(self.parent.id,
                                         inlet.parent.id, edge_id)
        self.inlets.append((inlet, edge_id))


class PdElement(object):
    def __init__(self, patch, id, *args):
        self.patch = patch
        self.id = id
        self.args = args
        self.ins = {}
        self.outlets = {}

    def inlet(self, index):
        if index not in self.ins:
            self.ins[index] = Inlet(self, index)
        return self.ins[index]

    def outlet(self, index):
        if index not in self.outlets:
            self.outlets[index] = Outlet(self, index)
        return self.outlets[index]

    def __getitem__(self, index):
        return InletOutlet(self, index)


class PdObject(PdElement):
    def __init__(self, patch, id, name, *args):
        super(PdObject, self).__init__(patch, id, *args)
        self.name = name

    def accept(self, render_visitor, ctx=None):
        render_visitor.visit_pd_obj(self, ctx=ctx)


class PdMessage(PdElement):
    def __init__(self, patch, id, *args):
        super(PdMessage, self).__init__(patch, id, *args)

    def accept(self, render_visitor, ctx=None):
        render_visitor.visit_pd_msg(self, ctx=ctx)


class PdPatch(object):
    def __init__(self, validate=False):
        self.graph = nx.MultiDiGraph()
        self.objects = {}
        self.seq = 0
        self._loadbang = None
        self.validate = validate

    def next_key(self):
        self.seq += 1
        return self.seq

    def _add_element(self, factory):
        node_id = self.next_key()
        self.graph.add_node(node_id)
        newelement = factory(node_id)
        self.objects[node_id] = newelement
        return newelement

    def obj(self, name, *args):
        return self._add_element(lambda node_id: PdObject(self, node_id, name, *args))

    def subpatch(self, name):
        return self._add_element(lambda node_id: PdSubPatch(self, node_id, name))

    def msg(self, *args):
        return self._add_element(lambda node_id: PdMessage(self, node_id, *args))

    def loadbang(self, inlet):
        if self._loadbang is None:
            self._loadbang = self.obj('loadbang')
        self._loadbang[0].to(inlet)

    def accept(self, render_visitor, ctx=None):
        render_visitor.visit_pd_patch(self, ctx=ctx)


# TODO force layout of inlets and outlets to have stable order
class PdSubPatch(PdElement):
    def __init__(self, patch, id, name):
        super(PdSubPatch, self).__init__(patch, id)
        self.subpatch = PdPatch()
        self.name = name

    def accept(self, render_visitor, ctx=None):
        render_visitor.visit_pd_subpatch(self, ctx=ctx)

    def __getattr__(self, name):
        if not hasattr(self.subpatch, name):
            raise AttributeError('No attribute with name ' + name)
        return getattr(self.subpatch, name)


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
        sorted_nodes = nx.topological_sort(patch.graph)

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