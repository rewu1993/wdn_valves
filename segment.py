import numpy as np
from scipy.sparse import csc_matrix
from scripts.grid import * 

class Segment(object):
    def __init__(self, sid):
        self.sid = sid
        self.nids = []
        self.pids = []
    def __str__(self):  
        return "segment with sid %d, links to nid %s and pid %s " % (
            self.sid, str(self.nids),str(self.pids)  )  
    
class PipeSegmentStat(object):
    def __init__(self,tot_num_pipes):
        self.tot_num_pipes = tot_num_pipes
        self.seg_pipes_num = self._init_seg_pipes_dict()
        self.seg_sizes_max = []
        self.seg_sizes_mean = []
        self.num_pipe_seg = 0 # non trivial
        
    def _init_seg_pipes_dict(self):
        pipe_num_dict = {}
        for i in range(1,self.tot_num_pipes):
            pipe_num_dict[i+1] = 0
        return pipe_num_dict
    
    def analyze_pipe_segs(self,pipe_segments):
        num_segs = []
        for segs in pipe_segments:
            num_segs.append(len(segs))
            num_pipes_sim = []
            for pipe_seg in segs:
                num_pipes_seg = len(pipe_seg.pids)
                num_pipes_sim.append(num_pipes_seg)
                self.seg_pipes_num[num_pipes_seg] += 1
            
            self.seg_sizes_max.append(np.max(num_pipes_sim))
            self.seg_sizes_mean.append(np.mean(num_pipes_sim))
        self.num_pipe_seg = np.mean(num_segs)

class PipeSegmentReport(object):
    def __init__(self,grid_size):
        self.tot_num_pipes = 2*(grid_size-1)*grid_size
        self.pipe_segments = [] #non trivial ones
        self.stat = PipeSegmentStat(self.tot_num_pipes)
    
    def update_stat(self):
        self.stat.analyze_pipe_segs(self.pipe_segments)

#     def __str__(self):  
#         return f"num_nontrivial_seg: {}, max_num_pipes number: {}, \
#         average_num_pipes {}, average_num_multipipe is {}, \
#         prob to multiseg {}" 


        
class SegmentReport(object):
    def __init__(self,grid_size):
        self.grid_size = grid_size
        self.num_sim = 0
        self.num_segments = []
        self.pipe_seg_report = PipeSegmentReport(grid_size)
    
    def __str__(self):  
        pipe_seg_ratio = self.num_pipe_segments/self.num_pipes
#         print (self.pipe_seg_report)
        return "pipes number:  %d, segment number: %d, pipe segment number %d, pipe_seg_ratio is %f" % (
            self.num_pipes, self.num_segments,self.num_pipe_segments, pipe_seg_ratio)  

    def get_segments_stats(self):
        self.pipe_seg_report.update_stat()
        return self.pipe_seg_report.stat
        
    
def assemble_adjacency_mtx(num_nodes_side,valves_dict):
    tot_nodes = num_nodes_side*num_nodes_side
    tot_pipes = 2*(num_nodes_side-1)*num_nodes_side
    tot_vertices = tot_nodes+tot_pipes
    rows,cols = [],[]
    
    for vid,valve in valves_dict.items():
        if valve.fail:
            rows.append(valve.nid)
            cols.append(valve.pid+tot_nodes)
            rows.append(valve.pid+tot_nodes)
            cols.append(valve.nid)
    vals = 1+np.zeros(len(rows))
    A = csc_matrix((vals, (rows, cols)), shape=(tot_vertices,tot_vertices))
    return A

def get_component(root,A):
    nids_to_explore = [root]
    component = []
    
    while len(nids_to_explore):
        nid = nids_to_explore.pop()
        if nid not in component:
            component.append(nid)
        
        row = A[nid,:]
        linked_nids = np.nonzero(row)[1]
        
        for linked_nid in linked_nids:
            if linked_nid not in component:
                nids_to_explore.append(linked_nid)
    return component
    
def bfs(A):
    nids = set(range(A.shape[0]))
    components = []
    while len(nids):
        bfs_root = nids.pop()
        component = get_component(bfs_root,A)
        nids -= set(component)
        components.append(component)
    return components


def create_segment(vid, component,num_nodes):    
    seg = Segment(vid)
    for element in component:
        if element < num_nodes:
            seg.nids.append(element)
        else:
            seg.pids.append(element-num_nodes)
    return seg
             
    
def find_segments(A, num_nodes):
    segments = []
    components = bfs(A)
    for i, component in enumerate(components):
        segment = create_segment(i, component,num_nodes)
        segments.append(segment)
    return segments


def fail_valves(valves_dict, fail_rate  = 0.5):
    for _,v in valves_dict.items():
        s = np.random.uniform(0,1,1)
        if s < fail_rate:
            v.fail = True
    return valves_dict

def update_segment_report(segments,report):
    report.num_sim += 1
    report.num_segments.append(len(segments)) 
    
    pipe_segments = []
    for segment in segments:
        if len(segment.pids) > 1: # only considering the non trivial cases
            pipe_segments.append(segment)
    report.pipe_seg_report.pipe_segments.append(pipe_segments)
    return report
    
def simulate_segments(grid_size,fail_rate):
    valves = generate_valves_grid(grid_size)
    valve_register = ValveRegister()
    register_valves(valves,valve_register)

    valves_dict = fail_valves(valve_register.vid2v,fail_rate)

    A = assemble_adjacency_mtx(grid_size,valves_dict)
    segments = find_segments(A,grid_size*grid_size)
    return segments

def generate_sim_report(grid_size,num_simulation,fail_rate):
    report = SegmentReport(grid_size,fail_rate)
    for i in range(num_simulation):
        segments = simulate_segments(grid_size,fail_rate)
        report = update_segment_report(segments,report)
    return report



