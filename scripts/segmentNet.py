from scripts.segment import *
from scripts.valves import *

class SegmentNet(object):
    def __init__(self,vstates,src_pids):
        self.vstates = vstates
        
        self.segments = simulate_segments(self.vstates)
        self.sid2index = self._init_sid2index()
        self.nid2seg = get_nid2seg_dict(self.segments)
        self.pid2seg = get_pid2seg_dict(self.segments)
        self.src_segments = self._get_src_segments(src_pids)
        self.seg_adj_mtx = self._init_seg_adj_mtx()
        
        self._init_segment_risk()
        self._init_segment_cost()
        self.exp_costs = [self._update_expected_cost()]
        self.pid_costs = [np.ones(len(self.pid2seg))]
    
    def _init_sid2index(self):
        sid2index = {}
        for i, seg in enumerate(self.segments):
            sid2index[seg.sid] = i
        return sid2index
    
    def _init_seg_adj_mtx(self):
        A = np.zeros((len(self.segments),len(self.segments)))
        linking_valves = self.vstates.normal_valves+self.vstates.white_valves
        for v in linking_valves:
            seg0 = self.nid2seg[v.nid]
            seg1 = self.pid2seg[v.pid]
            A[seg0.sid,seg1.sid] = 1
            A[seg1.sid,seg0.sid] = 1 # symmetry
        return A 
    
    def _get_src_segments(self,src_pids):
        src_segments = []
        for src_pid in src_pids:
            src_segments.append(self.pid2seg[src_pid])
        return src_segments
        
    def _find_isolated_sidx(self,A,seg_idx):
        src_components = []
        for src_seg in self.src_segments:
            src_index = self.sid2index[src_seg.sid]
            components,_ = bfs_tree(src_index,A)
            src_components+=components
            
        tot_sidx = set(range(len(self.segments)))
        tot_sidx.remove(seg_idx) # remove the isolated segment 
        
        isolated_sidx = tot_sidx- set(src_components)
        return isolated_sidx
        
    
    def _find_unintend_cost(self,seg_idx):
        A = copy.deepcopy(self.seg_adj_mtx)
        A[seg_idx,:] = 0
        A[:,seg_idx] = 0
        isolated_sidx = self._find_isolated_sidx(A,seg_idx)
        unintend_cost = 0
        for sidx in isolated_sidx:
            seg = self.segments[sidx]
            unintend_cost += seg.direct_cost
        return unintend_cost
    
    def _init_segment_risk(self):
        L = len(self.pid2seg)
        for i, seg in enumerate(self.segments):
            seg.adjust_risk(L)
        
    def _init_segment_cost(self):
        for i, seg in enumerate(self.segments):
            seg.adjust_direct_cost()
        # direct cost for a segment must be precomputed before finding unintend cost
        for i, seg in enumerate(self.segments):
            unintend_cost = self._find_unintend_cost(i)
            seg.unintend_cost = unintend_cost
            
    def _update_expected_cost(self):
        expected_cost = 0
        for seg in self.segments:
            if seg not in self.src_segments:
                tot_cost = seg.direct_cost+seg.unintend_cost
                expected_cost+= tot_cost*seg.risk
        return expected_cost
    
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
        seg_to.unintend_cost = self._find_unintend_cost(sindex2merge)
        return seg_to
    
    def _update_pid_cost(self):
        cost = np.zeros(len(self.pid2seg))
        for seg in self.segments:
            for pid in seg.pids:
                cost[pid] = seg.direct_cost+seg.unintend_cost
        self.pid_costs.append(cost)
        
    def valve_fail(self):
        failed_valve = self.vstates.fail_valves(1)[0]
        seg_from = self.nid2seg[failed_valve.nid]
        seg_to = self.pid2seg[failed_valve.pid]
        if seg_from != seg_to:
            merged_segment = self._merge_segment(seg_from,seg_to)
#         else:
#             print ('valve link to the same segment')
        self.exp_costs.append(self._update_expected_cost())
        self._update_pid_cost()
    
    @property 
    def vfail_rate(self):
        return self.vstates.fail_rate
        
        
        
def get_nid2seg_dict(segments):
    nid2seg = {}
    for seg in segments:
        for nid in seg.nids:
            nid2seg[nid] = seg
    return nid2seg

def get_pid2seg_dict(segments):
    pid2seg = {}
    for seg in segments:
        for pid in seg.pids:
            pid2seg[pid] = seg
    return pid2seg
        
            
            