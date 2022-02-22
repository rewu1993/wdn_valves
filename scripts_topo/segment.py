import numpy as np
from scripts_topo.grid import * 
from scripts_topo.graph import *
from scipy.sparse import lil_matrix

class Segment(object):
    def __init__(self, sid):
        self.sid = sid
        self.nids = []
        self.pids = []
        self.ids = []
       
    def __str__(self):  
        return "segment with sid %d, links to nid %s and pid %s " % (
            self.sid, str(self.nids),str(self.pids)  )  
    
class PipeSegmentStat(object):
    def __init__(self,tot_num_pipes):
        self.tot_num_pipes = tot_num_pipes
        self.seg_pipes_num = self._init_seg_pipes_dict()
        self.seg_sizes_max = []
        self.seg_sizes_mean = []
        self.num_pipe_seg = 0 
        self.num_multi_pipe_seg = 0
        
    def _init_seg_pipes_dict(self):
        pipe_num_dict = {}
        for i in range(self.tot_num_pipes):
            pipe_num_dict[i+1] = 0
        return pipe_num_dict
    
    def analyze_pipe_segs(self,pipe_segments):
        num_segs,num_multi_segs = [], []
        for segs in pipe_segments:
            num_segs.append(len(segs))
            num_pipes_sim = []
            for pipe_seg in segs:
                num_pipes_seg = len(pipe_seg.pids)
                num_pipes_sim.append(num_pipes_seg)
                self.seg_pipes_num[num_pipes_seg] += 1
            
            self.seg_sizes_max.append(np.max(num_pipes_sim))
            self.seg_sizes_mean.append(np.mean(num_pipes_sim))
            num_multi_segs.append(np.count_nonzero(np.array(num_pipes_sim)-1))
        self.num_pipe_seg = np.mean(num_segs)
        self.num_multi_pipe_seg = np.mean(num_multi_segs)

class PipeSegmentReport(object):
    def __init__(self,grid_size):
        self.tot_num_pipes = 2*(grid_size-1)*grid_size
        self.pipe_segments = []
        self.stat = PipeSegmentStat(self.tot_num_pipes)
    
    def update_stat(self):
        self.stat = PipeSegmentStat(self.tot_num_pipes)
        self.stat.analyze_pipe_segs(self.pipe_segments)

#     def __str__(self):  
#         return f"num_nontrivial_seg: {}, max_num_pipes number: {}, \
#         average_num_pipes {}, average_num_multipipe is {}, \
#         prob to multiseg {}" 

def create_segment(sid, component,num_nodes):    
    seg = Segment(sid)
    for element_id in component:
        seg.ids.append(element_id)
        if element_id < num_nodes:
            seg.nids.append(element_id)
        else:
            seg.pids.append(element_id-num_nodes)
    return seg
             
    
def find_segments(A, num_nodes):
    segments = []
    components = bfs(A)
    for i, component in enumerate(components):
        segment = create_segment(i, component,num_nodes)
        segments.append(segment)
    return segments

def update_segment_report(segments,report):
    report.num_sim += 1
    report.num_segments.append(len(segments)) 
    
    pipe_segments = []
    for segment in segments:
        if len(segment.pids) > 0: 
            pipe_segments.append(segment)
    report.pipe_seg_report.pipe_segments.append(pipe_segments)
    return report

class SegmentReport(object):
    def __init__(self,grid_size):
        self.grid_size = grid_size
        self.num_sim = 0
        self.segments = {}
        self.segment_graph = None
    
    def __str__(self):  
        pipe_seg_ratio = self.num_pipe_segments/self.num_pipes
#         print (self.pipe_seg_report)
        return "pipes number:  %d, segment number: %d, pipe segment number %d, pipe_seg_ratio is %f" % (
            self.num_pipes, self.num_segments,self.num_pipe_segments, pipe_seg_ratio)  

    def get_segments_stats(self,trivial_pids = {}):
        self.pipe_seg_report.update_stat(trivial_pids)
        return self.pipe_seg_report.stat
    
    
class SegmentSummary(object):
    def __init__(self,num_nodes,segments,A_diff,num_closed_pipes = 0):
        self.num_nodes = num_nodes
        self.segments = segments
        self.num_closed_pipes = num_closed_pipes
        self.pipe_sids = self._get_pipe_seg_ids()
        self.id2sid = self._get_id2sid()
        
        self.segment_graph = self.convert2seg_graph(A_diff)
        
    def _get_pipe_seg_ids(self):
        sids = []
        for seg in self.segments:
            if len(seg.pids):
                sids.append(seg.sid)
        return sids
    
    def _get_id2sid(self):
        id2sid ={}
        for sid, seg in enumerate(self.segments):
            for id in seg.ids:
                id2sid[id] = sid
        return id2sid
    
    def convert2seg_graph(self,A_diff):
        segment_graph = lil_matrix((len(self.segments), len(self.segments)), 
                                   dtype=np.int8)
        for i in range(A_diff.shape[0]):
            searching_sid = self.id2sid[i]
            nearby_ids = np.nonzero(A_diff[i,:])[1]
            for nearby_id in nearby_ids:
                nearby_sid = self.id2sid[nearby_id]
                segment_graph[searching_sid,nearby_sid] = 1  
                segment_graph[nearby_sid,searching_sid] = 1  
        return segment_graph
    
    
    def _get_unintend_consequence(self,segment_graph,iso_sids):
        components = bfs(segment_graph)
        unintend_consequence = 0
        for iso_component in components[1:]:
            for sid in iso_component:
                if sid not in iso_sids:
                    seg = self.segments[sid]
                    unintend_consequence += len(seg.pids)
#         print (iso_sids,components[0],unintend_consequence,self.num_closed_pipes)
        unintend_consequence -= self.num_closed_pipes
        
        return unintend_consequence
        
    def _iso_on_segment_graph(self,segment_graph,sid):
        segment_graph[sid,:] = 0
        segment_graph[:,sid] = 0
        return segment_graph
    
    def _iso_consequence(self,sids):
        segment_graph = self.segment_graph.copy()
        direct_consequence = 0
        for sid in sids:
            seg = self.segments[sid]
            direct_consequence += len(seg.pids)
            segment_graph = self._iso_on_segment_graph(segment_graph,sid)
        unintend_consequence = self._get_unintend_consequence(segment_graph,sids)
        return direct_consequence,unintend_consequence
        
    
    def pipe_iso_consequences(self,pids):
        direct_consequences = []
        unintend_consequences = []
        for pid in pids:
            id = self.num_nodes + pid
            sid = self.id2sid[id]
            direct,unintened = self._iso_consequence([sid])
            direct_consequences.append(direct)
            unintend_consequences.append(unintened)
        return np.array(direct_consequences),np.array(unintend_consequences)
            
                
    def _multi_pipe_iso_consequence(self,pids2close):
        sids = []
        for pid in pids2close:
            id = self.num_nodes + pid
            sids.append(self.id2sid[id])
        return self._iso_consequence(sids)
    
    
    def multi_pipe_iso_consequences(self,valid_pids,degree,num_sim = 100):
        np.random.seed()
        pids2close_pool = [np.random.choice(list(valid_pids),degree,replace = False) for _ in range(num_sim)]
        directs, unintends = [], []
        for pids2close in pids2close_pool:
            direct, unintend = self._multi_pipe_iso_consequence(pids2close)
            directs.append(direct)
            unintends.append(unintend)
        return np.mean(directs),np.mean(unintends)



    


        
        



   

