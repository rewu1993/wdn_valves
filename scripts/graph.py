import numpy as np
from scipy.sparse import csc_matrix

def assemble_adjacency_mtx(nnodes,npipes,valves_dict):
    tot_vertices = nnodes+npipes
    rows,cols = [],[]
    for vid,valve in valves_dict.items():
        if valve.fail:
            rows.append(valve.nid)
            cols.append(valve.pid+nnodes)
            rows.append(valve.pid+nnodes)
            cols.append(valve.nid)
    vals = 1+np.zeros(len(rows))
    A = csc_matrix((vals, (rows, cols)), shape=(tot_vertices,tot_vertices))
    return A


def create_adj_mtx(vstates):
    nnodes = len(vstates.vreg.nid2v)
    npipes = len(vstates.vreg.pid2v)
    vdict = vstates.get_valve_dict()
    A = assemble_adjacency_mtx(nnodes, npipes, vdict)
    return A

def explore_current_level(current_level,A,component):
    next_level = []
    for nid in current_level:
        row = A[nid,:]
        linked_nids = np.nonzero(row)[1]
        for linked_nid in linked_nids:
            if linked_nid not in component:
                next_level.append(linked_nid)
                component.add(linked_nid)
    return next_level


def bfs_tree(root,A):
    nids_to_explore = [root]
    component = []
    edges = []
  
    while len(nids_to_explore):
        nid = nids_to_explore.pop()
        if nid not in component:
            if (len(component)):
                edges.append((component[-1],nid))
            component.append(nid)
        row = A[nid,:]
        try:
            linked_nids = np.nonzero(row)[1]
        except:
            linked_nids = np.nonzero(row)[0]
            
        for linked_nid in linked_nids:
            if linked_nid not in component:
                nids_to_explore.append(linked_nid)
    return component,edges

    
    
def bfs(A):
    nids = set(range(A.shape[0]))
    components = []
    while len(nids):
        bfs_root = nids.pop()
        component, _ = bfs_tree(bfs_root,A)
        nids -= set(component)
        components.append(component)
    return components

