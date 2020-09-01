from scripts.graph import *
from scripts.grid import *
from scripts.node import *
from scripts.topology_operations import *

"""Utility functions """
def check_left_right(left_node,right_node):
    left_node_valves = left_node.valve_neighbors
    right_node_valves = right_node.valve_neighbors
    if (not left_node_valves.right.fail) and (not right_node_valves.left.fail):
        return True
    return False

def check_up_down(up_node,down_node):
    up_node_valves = up_node.valve_neighbors
    down_node_valves = down_node.valve_neighbors
    if (not up_node_valves.down.fail) and (not down_node_valves.up.fail):
        return True
    return False
        
def check_direct_linkage(node1,node2):
    n1_neighbors = node1.get_node_neighbor_ids()
    nid2 = node2.nid
    if nid2 not in n1_neighbors:
        return False
    
    if n1_neighbors[0] == nid2:
        return check_left_right(node2,node1)
    if n1_neighbors[1] == nid2:
        return check_left_right(node1,node2)
    if n1_neighbors[2] == nid2:
        return check_up_down(node2,node1)
    if n1_neighbors[3] == nid2:
        return check_up_down(node1,node2)

def get_direct_link_nodes(node,nids2node):
    neighbors = node.get_node_neighbor_ids()
    linked_nodes = []
    for nid in neighbors:
        if (nid!=None):
            neighbor_node = nids2node[nid]
            if check_direct_linkage(node,neighbor_node):
                linked_nodes.append(neighbor_node)
    return linked_nodes

def assemble_adjacency_mtx_nodes(nids2node):
    tot_nodes = len(nids2node)
    rows,cols = [],[]
    for nid,node in nids2node.items():
        connected_nodes = get_direct_link_nodes(node,nids2node)
        for connected_node in connected_nodes:
            rows.append(nid)
            cols.append(connected_node.nid)

    vals = 1+np.zeros(len(rows))
    A = csc_matrix((vals, (rows, cols)), shape=(tot_nodes,tot_nodes))
    return A

def node_pair2pid(node1,node2):
    pids1 = set(node1.get_pipe_neighbor_ids())
    pids2 = set(node2.get_pipe_neighbor_ids())
    pids = pids1.intersection(pids2)
    
    pid = None 
    for p in pids:
        if p!= None:
            pid = p
    return pid

def convert_npairs2pids(node_pairs,nids2node):
    pids = []
    for nid1,nid2  in node_pairs:
        n1,n2 = nids2node[nid1],nids2node[nid2]
        pids.append(node_pair2pid(n1,n2))
    return pids

def get_bfs_edges(A,nids2node):
    component,edges = bfs_tree(0,A)
    edges = convert_npairs2pids(edges,nids2node) 
    return edges

def choose_pid2close(node,pid_blacklist):
    valid_pids = []
    pids = [pid for pid in node.pipe_neighbors if (pid != None and pid not in pid_blacklist) ]
    if len(pids):
        return np.random.choice(pids,1)[0]
    else:
        return None
    

"""The Mesh Class"""

class Mesh(object):
    def __init__(self,grid_size):
        self.grid_size = grid_size
        self.nids = set(range(grid_size*grid_size))
        
        self.valve_register = self._create_valveNregister()
        self.nid2nodes = self._create_nid2nodes()
        self.contraction_reg = ContractionRegister()
        self._init_degree_distribution()
        
        self.adj_mtx_nodes = assemble_adjacency_mtx_nodes(self.nid2nodes)
        self.bfs_edges = get_bfs_edges(self.adj_mtx_nodes,self.nid2nodes)
        self.closed_pids = set()
        
    def _create_valveNregister(self):
        valves = generate_valves_grid(self.grid_size)
        valve_register = ValveRegister()
        valve_register.register(valves)
        return valve_register
    
    def _create_nid2nodes(self):
        return get_nid2nodes(self.grid_size,self.valve_register.nid2v)
    
    def _init_degree_distribution(self):
        self.degree_distribution = {}
        for i in range(10):
            self.degree_distribution[i] = []
    
    def close_pipe_on_node(self,nid,pid2close):
        node1 = self.nid2nodes[nid]
        op = None
        for i, pid in enumerate(node1.pipe_neighbors):
            if pid ==  pid2close:
                node1.closed_pipes[i] = True
                op = i
                break
        if op == None:
            raise Exception(f"can not close pipe {pid2close}, not linked to this node")
            
        nid2 = node1.get_node_neighbor_ids()[op]
        node2 = self.nid2nodes[nid2]
        self._close_pipe_on_other_end(node2,op)
        self.update_degree_distribution()
            
    def _close_pipe_on_other_end(self,node2,op):
        if op == 0:
            node2.closed_pipes[1] = True
        elif op == 1:
            node2.closed_pipes[0] = True
        elif op == 2:
            node2.closed_pipes[3] = True
        elif op == 3:
            node2.closed_pipes[2] = True
            
    def _vids2open(self):
        contraction_reg = self.contraction_reg
        vids2open = []
        for v1,v2 in contraction_reg.vpairs:
            vids2open.append(v1.vid)
            vids2open.append(v2.vid)
        return vids2open


    def _vids2close(self):
        vids2close = []
        for pid in self.closed_pids:
            v1,v2 = self.valve_register.pid2v[pid]
            vids2close.append(v1.vid)
            vids2close.append(v2.vid)
        return vids2close
             
    def get_closed_pids(self):
        return self.closed_pids
    
    def get_open_pids(self):
        return self.contraction_reg.trivial_pids
    
    @property
    def valid_vids(self):
        topo_vids = set(self._vids2close()+self._vids2open())
        valid_vids = list(set(self.valve_register.vid2v.keys())-topo_vids)
        return valid_vids
    
    @property
    def valid_pids(self):
        full_pids = set(range(len(self.valve_register.pid2v)))
        valid_pids = full_pids - set(self.get_closed_pids())
        valid_pids -= set(self.get_open_pids())
        return valid_pids
    
    def update_degree_distribution(self):    
        self._init_degree_distribution()
        normal_nids = self.nids-self.contraction_reg.contracted_nids
        for normal_nid in normal_nids:
            node = self.nid2nodes[normal_nid]
            degree = node.degree()
            self.degree_distribution[degree].append(normal_nid)
        
        for cn1,cn2 in self.contraction_reg.npairs:
            degree = cn1.degree()+cn2.degree()-2
            self.degree_distribution[degree].append(cn1.nid)
    
    def perform_contractions(self,identify_pairs_op):
        self.contraction_reg = register_contractions(identify_pairs_op,self.contraction_reg)
        self.update_degree_distribution()
        self.valve_register.update_open_valves(self._vids2open()) #update valve register
        
    
    def reduce_degree_num(self,degree,desired_num,max_steps = 1000):
        self.update_degree_distribution()
        nids = self.degree_distribution[degree]
        step = 0
        while (len(nids) > desired_num):
            if step > max_steps: 
                raise Exception(f"Fail to reduce number of {degree} to {desired_num}")
            nid2close = np.random.choice(nids,1)[0]
            node2close = self.nid2nodes[nid2close]
            pid2close = choose_pid2close(node2close,self.bfs_edges)
            if pid2close != None:
                self.close_pipe_on_node(nid2close,pid2close)
                self.closed_pids.add(pid2close)
                
            nids = self.degree_distribution[degree]
            step+=1
        
        self.valve_register.update_closed_valves(self._vids2close()) #update valve register
    




        
       