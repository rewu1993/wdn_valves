import numpy as np
from scripts.valves import * 

def generate_base_node_sequence_row(N):
    row_nodes = np.zeros(2*N-2)
    row_nodes[-1] = N-1
    pairs = []
    num_pairs = int((len(row_nodes)-2)/2)
    for i in range(num_pairs):
        pairs.append(i+1)
        pairs.append(i+1)
    row_nodes[1:-1] = np.array(pairs)
    return row_nodes.astype('int')
    
    
def generate_node_sequence_row(row_num,N):
    base = generate_base_node_sequence_row(N)
    return base+row_num*N


def generate_base_pipe_sequence_row(P):
    pairs = []
    num_pairs = P
    for i in range(num_pairs):
        pairs.append(i)
        pairs.append(i)
    return np.array(pairs)

def generate_pipe_sequence_row(row_num,P):
    base = generate_base_pipe_sequence_row(P)
    return base+row_num*P


def generate_valve_sequence_row(row_num,num_nodes_side):
    nids = generate_node_sequence_row(row_num,num_nodes_side)
    pids = generate_pipe_sequence_row(row_num,num_nodes_side-1)
    
    V = 2*num_nodes_side-2
    vid = row_num*V
    valves = []
    for nid,pid in zip(nids,pids):
        valve = Valve(vid,nid,pid)
        vid+=1
        valves.append(valve)
    return valves

def generate_valve_sequence_rows(num_nodes_side):
    valves = []
    for i in range(num_nodes_side):
        valves += generate_valve_sequence_row(i,num_nodes_side)
    return valves

def generate_pipe_sequence_col(col_num,num_nodes_side):
    num_pipes_side = num_nodes_side-1
    num_pipes_rows = num_nodes_side*num_pipes_side
    return generate_pipe_sequence_row(col_num,num_pipes_side)+num_pipes_rows

def generate_base_node_sequence_col(N):
    row_nodes = np.zeros(2*N-2)
    row_nodes[-1] = (N-1)*N
    pairs = []
    num_pairs = int((len(row_nodes)-2)/2)
    for i in range(num_pairs):
        pairs.append((i+1)*N)
        pairs.append((i+1)*N)
    row_nodes[1:-1] = np.array(pairs)
    return row_nodes.astype('int')
    
def generate_node_sequence_col(col_num,N):
    base = generate_base_node_sequence_col(N)
    return base+col_num

def generate_valve_sequence_col(col_num,num_nodes_side):
    nids = generate_node_sequence_col(col_num,num_nodes_side)
    pids = generate_pipe_sequence_col(col_num,num_nodes_side)
    
    V = 2*num_nodes_side-2
    vid = num_nodes_side*V+col_num*V
    valves = []
    for nid,pid in zip(nids,pids):
        valve = Valve(vid,nid,pid)
        vid+=1
        valves.append(valve)
    return valves

def generate_valve_sequence_cols(num_nodes_side):
    valves = []
    for i in range(num_nodes_side):
        valves += generate_valve_sequence_col(i,num_nodes_side)
    return valves

def generate_valves_grid(num_nodes_side):
    row_valves = generate_valve_sequence_rows(num_nodes_side)
    col_valves = generate_valve_sequence_cols(num_nodes_side)
    
    return row_valves+col_valves