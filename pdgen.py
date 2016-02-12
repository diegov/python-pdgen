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


class PdObject(object):
    def __init__(self, patch, id, name, *args):
        self.patch = patch
        self.id = id
        self.name = name
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


class PdPatch(object):
    def __init__(self):
        self.graph = nx.MultiDiGraph()
        self.objects = {}
        self.seq = 0

    def next_key(self):
        self.seq += 1
        return self.seq

    def obj(self, name, *args):        
        node_id = self.next_key()
        self.graph.add_node(node_id)
        newobj = PdObject(self, node_id, name, *args)
        self.objects[node_id] = newobj
        return newobj

    
def render(patch):

    height = 1000
    width  = 1000

    result = '#N canvas 1000 1000 1000 1000 10;\n'
    out_indices = {}
    positions = nx.spring_layout(patch.graph)
    sorted_nodes = nx.topological_sort(patch.graph)
    
    for ndx, id in enumerate(sorted_nodes):
        pd_obj = patch.objects[id]
        out_indices[id] = ndx
        x_pos = int(positions[id][0] * width)
        y_pos = int(positions[id][1] * height)
        args = ''
        for arg in pd_obj.args:
            args += ' ' + str(arg)
        line = "#X obj %u %u %s%s;\n" % (x_pos, y_pos, pd_obj.name, args)
        result += line

    for id in sorted_nodes:
        pd_obj = patch.objects[id]
        for out_ndx in sorted(pd_obj.outlets.keys()):
            outlet = pd_obj.outlets[out_ndx]
            for inlet, edge_id in outlet.inlets:
                out_obj_ndx = out_indices[outlet.parent.id]
                in_obj_ndx = out_indices[inlet.parent.id]
                line = "#X connect %u %u %u %u\n" % \
                       (out_obj_ndx, outlet.index, in_obj_ndx, inlet.index)
                result += line

    return result


#g = nx.DiGraph()

#g.add_node(1)

