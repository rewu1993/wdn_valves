import numpy as np
from scripts.graph import *


class Segment(object):
    def __init__(self, sid):
        self.sid = sid
        self.nids = []
        self.pids = []
        self.components = [sid]
        
        self.risk = 0
        self.direct_cost = 0
        self.unintend_cost = 0
       
    def __str__(self):  
        
        return "segment with sid %d, contains nid %s and pid %s, risk %f, direct_cost %f, unintend_cost %s  " % (
            self.sid, str(self.nids),str(self.pids),self.risk, self.direct_cost,str(self.unintend_cost)  )
    
    # merge two segments 
    def __iadd__(self, seg1):
        self.nids += seg1.nids
        self.pids += seg1.pids
        self.components += seg1.components
        self.risk += seg1.risk
        self.direct_cost += seg1.direct_cost
        self.unintend_cost = None # undefined, need to be recomputed
        return self
    
    def adjust_risk(self,L):
        self.risk = len(self.pids)/L
        return True
    
    def adjust_direct_cost(self):
        self.direct_cost = len(self.pids)
        
        

def create_segment_from_nullid(sid, component,num_nodes):    
    seg = Segment(sid)
    for element_id in component:
        if element_id < num_nodes:
            seg.nids.append(element_id)
        else:
            seg.pids.append(element_id-num_nodes)
    return seg

def find_segments(A, num_nodes):
    segments = []
    components = bfs(A)
    for i, component in enumerate(components):
        segment = create_segment_from_nullid(i, component,num_nodes)
        segments.append(segment)
    return segments

    
def simulate_segments(vstates):
    A = create_adj_mtx(vstates)
    nnodes = len(vstates.vreg.nid2v)
    segments = find_segments(A,nnodes)
    return segments