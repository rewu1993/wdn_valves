import numpy as np
import networkx as nx

from scripts.graph import *
from scripts.utils import * 



class Segment(object):
    @staticmethod
    def calculate_merge_direct_cost(seg1,seg2):
        num = (seg1.mean_direct_cost*len(seg1.pids)+
               seg2.mean_direct_cost*len(seg2.pids))
        dem = len(seg1.pids)+len(seg2.pids)
        
        return num/dem
        
    def __init__(self, sid):
        self.sid = sid
        self.nids = []
        self.pids = []
        self.components = [sid]
        
        self.fail_prob = 0
        self.mean_direct_cost = 0
        self.mean_unintend_cost = 0
       
    def __str__(self):  
        return "segment with sid %d, contains nid %s and pid %s, fail prob %f, mean_direct_cost %f, mean_unintend_cost %f  " % (
            self.sid, str(self.nids),str(self.pids),self.fail_prob, 
            self.mean_direct_cost,self.mean_unintend_cost)
    
    # merge two segments 
    def __iadd__(self, seg1):
        self.nids += seg1.nids
        self.pids += seg1.pids
        self.components += seg1.components
        self.fail_prob += seg1.fail_prob
        self.mean_direct_cost = Segment.calculate_merge_direct_cost(self,seg1)
        return self
    
    def update_fail_prob(self,N):
        self.fail_prob = len(self.pids)/N
        
    def update_mean_direct_cost(self,pid2pcost):
        tot_cost = 0
        for pid in self.pids:
            tot_cost += pid2pcost[pid]
        self.mean_direct_cost = tot_cost/len(self.pids)

class HydroSegmentNet(object):
    def __init__(self,vstates,src_pids,pid2pcost):
        self.vstates = vstates
        self.segments = self._init_segments(pid2pcost)
        self.sid2index = self._init_sid2index()
        self.nid2seg = get_nid2seg_dict(self.segments)
        self.pid2seg = get_pid2seg_dict(self.segments)
        self.src_segments = self._get_src_segments(src_pids)
        self.seg_adj_mtx = self._init_seg_adj_mtx()
        self.sids2vid = {}
        self.G = self._init_graph()
        self.merged_vids = []
        
    def _init_segments(self,pid2pcost):
        segments = simulate_segments(self.vstates)
        for seg in segments:
            if len(seg.pids) >0:
                seg.update_fail_prob(3000)
                seg.update_mean_direct_cost(pid2pcost)
        return segments
            
        
    def _init_sid2index(self):
        sid2index = {}
        for i, seg in enumerate(self.segments):
            sid2index[seg.sid] = i
        return sid2index
    
    def _init_seg_adj_mtx(self):
        A = np.zeros((len(self.segments),len(self.segments)))
        linking_valves = self.vstates.normal_valves+self.vstates.fixed_valves
        for v in linking_valves:
            seg0 = self.nid2seg[v.nid]
            seg1 = self.pid2seg[v.pid]
            A[seg0.sid,seg1.sid] = 1
            A[seg1.sid,seg0.sid] = 1 # symmetry
        return A 
    
    def _init_graph(self):
        G = nx.Graph()
        linking_valves = self.vstates.normal_valves+self.vstates.fixed_valves
        for v in linking_valves:
            seg0 = self.nid2seg[v.nid]
            seg1 = self.pid2seg[v.pid]
            G.add_nodes_from([seg0.sid,seg1.sid])
            G.add_edges_from([(seg0.sid,seg1.sid)])
            self.sids2vid[(seg0.sid,seg1.sid)] = v.vid
            self.sids2vid[(seg1.sid,seg0.sid)] = v.vid
        return G
    
    def _get_src_segments(self,src_pids):
        src_segments = []
        for src_pid in src_pids:
            src_segments.append(self.pid2seg[src_pid])
        return src_segments

    def _adjust_index_mapping(self,sindex2delete):
        # sid2index 
        for sid,sindex in self.sid2index.items():
            if sindex:
                if sindex > sindex2delete:
                    self.sid2index[sid] -= 1
                elif sindex== sindex2delete:
                    self.sid2index[sid] = None
                    
        # nid/pid mappings
        self.nid2seg = get_nid2seg_dict(self.segments)
        self.pid2seg = get_pid2seg_dict(self.segments)
        
    def _adjust_seg_adj_mtx(self,sindex2delete,sindex2merge):
        self.seg_adj_mtx[sindex2merge,:] += self.seg_adj_mtx[sindex2delete,:]
        self.seg_adj_mtx[:,sindex2merge] += self.seg_adj_mtx[:,sindex2delete]
        
        self.seg_adj_mtx = np.delete(self.seg_adj_mtx,sindex2delete,0)
        self.seg_adj_mtx = np.delete(self.seg_adj_mtx,sindex2delete,1)
        
                
    def _merge_segment(self,seg_from,seg_to):
        seg_to += seg_from 
        
        sindex2delete = self.sid2index[seg_from.sid]
        sindex2merge = self.sid2index[seg_to.sid]
        self.segments.pop(sindex2delete)
        
        self._adjust_seg_adj_mtx(sindex2delete,sindex2merge)
        self._adjust_index_mapping(sindex2delete)
        
        sindex2merge = self.sid2index[seg_to.sid] # index mapping has changed
        return seg_to
    
    def evaluate_merge(self,valve):
        seg_from = self.nid2seg[valve.nid]
        seg_to = self.pid2seg[valve.pid]
        if seg_from == seg_to:
            return 9999999999999999
        merged_cost = (Segment.calculate_merge_direct_cost(seg_from,seg_to)*
                       (len(seg_from.pids)+len(seg_to.pids)))
        
        additional_cost = (seg_from.fail_prob*(merged_cost-seg_from.mean_direct_cost*len(seg_from.pids))+
                         seg_to.fail_prob*(merged_cost-seg_to.mean_direct_cost)*len(seg_to.pids))
        return additional_cost
    
    def optimal_merge(self):
        optimal_merge_segments = (None,None)
        min_additional_cost = 99999999999999
        vid = -1
        for vidx, valve in enumerate(self.vstates.normal_valves):
            additional_cost = self.evaluate_merge(valve)
            if additional_cost<min_additional_cost:
                min_additional_cost = additional_cost
#                 print (self.evaluate_merge(valve))
                seg_from = self.nid2seg[valve.nid]
                seg_to = self.pid2seg[valve.pid]
                optimal_merge_segments = (seg_from,seg_to)
                vid = valve.vid
        
        merged_segment = self._merge_segment(optimal_merge_segments[0],
                                            optimal_merge_segments[1])
#         print (merged_segment.mean_direct_cost)
        self.merged_vids.append(vid)
        
        
    def optimal_valve_reduction(self,num_failed_valves):
        for i in range(num_failed_valves):
            self.optimal_merge()
    
    def fail_valve(self, valve):
        vidx = -1
        for i,v in enumerate(self.vstates.normal_valves):
            if v == valve:
                vidx = i
        self.vstates.fail_valve(vidx)
        seg_from = self.nid2seg[valve.nid]
        seg_to = self.pid2seg[valve.pid]
        if seg_from != seg_to:
            merged_segment = self._merge_segment(seg_from,seg_to)
        
        
        
    def valve_fail(self):
        failed_valve = self.vstates.fail_valves(1)[0]
        seg_from = self.nid2seg[failed_valve.nid]
        seg_to = self.pid2seg[failed_valve.pid]
        if seg_from != seg_to:
            merged_segment = self._merge_segment(seg_from,seg_to)
            
            
    @property 
    def vfail_rate(self):
        return self.vstates.fail_rate
    
    @property
    def valid_pipe_segments(self):
        valid_segments = []
        for seg in self.segments:
            if seg not in self.src_segments:
                if len(seg.pids) > 0:
                    valid_segments.append(seg)
        return valid_segments
    
    @property
    def system_direct_cost(self):
        tot_cost = 0
        for seg in self.valid_pipe_segments: 
            cost = seg.fail_prob*len(seg.pids)*seg.mean_direct_cost
#             print (cost)
#             print (seg.fail_prob,len(seg.pids),seg.mean_direct_cost)
            tot_cost += cost 
        return tot_cost
        
        

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