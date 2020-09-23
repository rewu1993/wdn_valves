from wntr.sim.hydraulics import *
from wntr.network.model import *

import numpy as np
import warnings
import time
import sys
import logging
import scipy.sparse
import scipy.sparse.csr
import itertools

logger = logging.getLogger(__name__)


class WaterNetworkSimulator(object):
    """
    Base water network simulator class.

    wn : WaterNetworkModel object
        Water network model

    mode: string (optional)
        Specifies whether the simulation will be demand-driven (DD) or
        pressure dependent demand (PDD), default = DD
    """

    def __init__(self, wn=None, mode='DD'):

        self._wn = wn
        self.mode = mode

    def _get_link_type(self, name):
        if isinstance(self._wn.get_link(name), Pipe):
            return 'pipe'
        elif isinstance(self._wn.get_link(name), Valve):
            return 'valve'
        elif isinstance(self._wn.get_link(name), Pump):
            return 'pump'
        else:
            raise RuntimeError('Link name ' + name + ' was not recognised as a pipe, valve, or pump.')

    def _get_node_type(self, name):
        if isinstance(self._wn.get_node(name), Junction):
            return 'junction'
        elif isinstance(self._wn.get_node(name), Tank):
            return 'tank'
        elif isinstance(self._wn.get_node(name), Reservoir):
            return 'reservoir'
        elif isinstance(self._wn.get_node(name), Leak):
            return 'leak'
        else:
            raise RuntimeError('Node name ' + name + ' was not recognised as a junction, tank, reservoir, or leak.')


class NetworkRepresentor(WaterNetworkSimulator):
    """
    WNTR simulator class.
    The WNTR simulator uses a custom newton solver and linear solvers from scipy.sparse.

    Parameters
    ----------
    wn : WaterNetworkModel object
        Water network model

    mode: string (optional)
        Specifies whether the simulation will be demand-driven (DD) or
        pressure dependent demand (PDD), default = DD
    """

    def __init__(self, wn, mode='DD'):

        super(NetworkRepresentor, self).__init__(wn, mode)
        self._model = HydraulicModel(self._wn, self.mode)
        self._initialize_internal_graph()


    def _initialize_internal_graph(self):
        n_links = {}
        rows = []
        cols = []
        vals = []
        for link_name, link in itertools.chain(self._wn.pipes(), self._wn.pumps(), self._wn.valves()):
            from_node_name = link.start_node_name
            to_node_name = link.end_node_name
            from_node_id = self._model._node_name_to_id[from_node_name]
            to_node_id = self._model._node_name_to_id[to_node_name]
            if (from_node_id, to_node_id) not in n_links:
                n_links[(from_node_id, to_node_id)] = 0
                n_links[(to_node_id, from_node_id)] = 0
            n_links[(from_node_id, to_node_id)] += 1
            n_links[(to_node_id, from_node_id)] += 1
            rows.append(from_node_id)
            cols.append(to_node_id)
            rows.append(to_node_id)
            cols.append(from_node_id)
            if link.status == wntr.network.LinkStatus.closed:
                vals.append(0)
                vals.append(0)
            else:
                vals.append(1)
                vals.append(1)

        self._internal_graph = scipy.sparse.csr_matrix((vals, (rows, cols)))


        ndx_map = {}
        for link_name, link in self._wn.links():
            ndx1 = None
            ndx2 = None
            from_node_name = link.start_node_name
            to_node_name = link.end_node_name
            from_node_id = self._model._node_name_to_id[from_node_name]
            to_node_id = self._model._node_name_to_id[to_node_name]
            link_id = self._model._link_name_to_id[link_name]
            ndx_map[link_id] = (from_node_id, to_node_id)
        self.lid2npair = ndx_map

        self._number_of_connections = [0 for i in range(self._model.num_nodes)]
        for node_id in self._model._node_ids:
            self._number_of_connections[node_id] = self._internal_graph.indptr[node_id+1] - self._internal_graph.indptr[node_id]

        
        self._node_pairs_with_multiple_links = {}
        for from_node_id, to_node_id in n_links.keys():
            if n_links[(from_node_id, to_node_id)] > 1:
                if (to_node_id, from_node_id) in self._node_pairs_with_multiple_links:
                    continue
                self._internal_graph[from_node_id, to_node_id] = 0
                self._internal_graph[to_node_id, from_node_id] = 0
                from_node_name = self._model._node_id_to_name[from_node_id]
                to_node_name = self._model._node_id_to_name[to_node_id]
                tmp_list = self._node_pairs_with_multiple_links[(from_node_id, to_node_id)] = []
                for link_name in self._wn.get_links_for_node(from_node_name):
                    link = self._wn.get_link(link_name)
                    if link.start_node_name == to_node_name or link.end_node_name == to_node_name:
                        tmp_list.append(link)
                        if link.status != wntr.network.LinkStatus.closed:
                            ndx1, ndx2 = ndx_map[link]
                            self._internal_graph.data[ndx1] = 1
                            self._internal_graph.data[ndx2] = 1


    def get_isolated_junctions_and_links(self):

        node_set = [1 for i in range(self._model.num_nodes)]

        def grab_group(node_id):
            node_set[node_id] = 0
            nodes_to_explore = set()
            nodes_to_explore.add(node_id)
            indptr = self._internal_graph.indptr
            indices = self._internal_graph.indices
            data = self._internal_graph.data
            num_connections = self._number_of_connections

            while len(nodes_to_explore) != 0:
                node_being_explored = nodes_to_explore.pop()
                ndx = indptr[node_being_explored]
                number_of_connections = num_connections[node_being_explored]
                vals = data[ndx:ndx+number_of_connections]
                cols = indices[ndx:ndx+number_of_connections]
                for i, val in enumerate(vals):
                    if val == 1:
                        col = cols[i]
                        if node_set[col] ==1:
                            node_set[col] = 0
                            nodes_to_explore.add(col)

        for tank_name, tank in self._wn.nodes(wntr.network.Tank):
            tank_id = self._model._node_name_to_id[tank_name]
            if node_set[tank_id] == 1:
                grab_group(tank_id)
            else:
                continue

        for reservoir_name, reservoir in self._wn.nodes(wntr.network.Reservoir):

            reservoir_id = self._model._node_name_to_id[reservoir_name]
            grab_group(reservoir_id)
            
            if node_set[reservoir_id] == 1:
                grab_group(reservoir_id)
            else:
                continue

        isolated_junction_ids = [i for i in range(len(node_set)) if node_set[i] == 1]
        isolated_junctions = set()
        isolated_links = set()
        for j_id in isolated_junction_ids:
            j = self._model._node_id_to_name[j_id]
            isolated_junctions.add(j)
            print (j)
            connected_links = self._wn.get_links_for_node(j)
            for l in connected_links:
                isolated_links.add(l)
        isolated_junctions = list(isolated_junctions)
        isolated_links = list(isolated_links)

        return isolated_junctions, isolated_links

    def internal_graph(self):
        return self._internal_graph

    def nid2name(self,nid):
        return self._model._node_id_to_name[nid]

    def lid2name(self,lid):
        return self._model._link_id_to_name[lid]


