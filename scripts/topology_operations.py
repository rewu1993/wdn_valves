import numpy as np

"""Contraction""" 
class ContractionRegister(object):
    def __init__(self):
        self.npairs = []
        self.vpairs = []
        self.contracted_nids = set()
        self.trivial_pids = []
        
    def __str__(self):  
        return f"npairs: {self.npairs}, vpairs: {self.vpairs},\
        trivial_pids: {self.trivial_pids},contracted_nids: {self.contracted_nids}" 

def rand_operation():
    return np.random.choice(range(4),1)[0]

def potential_identify_id(node,op):
    neighbors = node.node_neighbors
    if op == 0:
        return neighbors.left
    elif op == 1:
        return neighbors.right
    elif op == 2:
        return neighbors.up
    elif op == 3:
        return neighbors.down
    
def valid_nid(nid,nids2identify):
    if (nid in nids2identify) or (nid == None):
        return False
    return True

def get_op_nid2identify(node,nids2identify):
    op = rand_operation()
    candidate = potential_identify_id(node,op)
    max_step = 1e3
    step = 0
    while not valid_nid(candidate, nids2identify):
        op = rand_operation()
        candidate = potential_identify_id(node,op)
        step+=1 
        if step > max_step:
            raise Exception('fail to contract')
    return op,candidate
        
def get_valves2open(node1,node2,op):
    vneighbors1 = node1.valve_neighbors
    vneighbors2 = node2.valve_neighbors
    
    if op == 0:
        v2open1,v2open2 = vneighbors1.left,vneighbors2.right
    elif op == 1:
        v2open1,v2open2 = vneighbors1.right,vneighbors2.left
    elif op == 2:
        v2open1,v2open2 = vneighbors1.up,vneighbors2.down
    elif op == 3:
        v2open1,v2open2 = vneighbors1.down,vneighbors2.up
    return (v2open1,v2open2)
    
def get_nids2identify(grid_size,ratio=0.2):
    N = grid_size*grid_size
    num_contraction = int(ratio*N/(1+ratio))
    identify_nids = np.random.choice([i for i in range(N)], num_contraction, replace=False)
    return set(identify_nids)

def get_identify_pairs_op(nids2identify,nid2node):
    identify_pairs_op = []
    for nid in nids2identify:
        node = nid2node[nid]
        op,nid2identify = get_op_nid2identify(node,nids2identify)
        node2identify = nid2node[nid2identify]
        identify_pairs_op.append((node,node2identify,op))
    return identify_pairs_op

def register_contractions(node_pairs_op,register):
    for node1, node2 ,op  in node_pairs_op:
        v1,v2 = get_valves2open(node1, node2 ,op)
        register.npairs.append((node1,node2))
        register.vpairs.append((v1,v2))
        register.contracted_nids.add(node1.nid)
        register.contracted_nids.add(node2.nid)
        register.trivial_pids.append(v1.pid)
    return register
        
    