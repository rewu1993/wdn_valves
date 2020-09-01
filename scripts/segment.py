import numpy as np
from scripts.grid import * 
from scripts.graph import *

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


def fail_valves(valves_dict, vids2fail):
    for vid,v in valves_dict.items():
        if vid in vids2fail:
            v.fail = True
    return valves_dict

def update_segment_report(segments,report):
    report.num_sim += 1
    report.num_segments.append(len(segments)) 
    
    pipe_segments = []
    for segment in segments:
        if len(segment.pids) > 0: 
            pipe_segments.append(segment)
    report.pipe_seg_report.pipe_segments.append(pipe_segments)
    return report
    
def simulate_segments(grid_size,valves_dict):
    A = assemble_adjacency_mtx(grid_size,valves_dict)
    segments = find_segments(A,grid_size*grid_size)
    return segments


def generate_valves_dict(valve_register,x,fail_rate):
    valve_register.recover_valves()
    if x == 0:
        vids2fail = generate_vids2fail(list(valve_register.vid2v.keys()),fail_rate)
    else:
        # N-x setting 
        config_fvids,remained_vids = generate_nx_config(valve_register,x)
        vids2fail = generate_vids2fail(remained_vids,fail_rate)
        vids2fail+= config_fvids
    valves_dict = fail_valves(valve_register.vid2v,vids2fail)
    return valves_dict
    

def generate_sim_report_nx(grid_size,num_simulation,x,fail_rate):
    report = SegmentReport(grid_size)
    valves = generate_valves_grid(grid_size)
    valve_register = ValveRegister()
    register_valves(valves,valve_register)
    for i in range(num_simulation):
        valves_dict = generate_valves_dict(valve_register,x,fail_rate)
        segments = simulate_segments(grid_size,valves_dict)
        report = update_segment_report(segments,report)
    return report

def generate_nx_config(valve_register,x):
    nid2valve = valve_register.nid2v
    vids2fail = []
    for _,valves in nid2valve.items():
        removed_valves = np.random.choice(valves, x, replace=False)
        for removed_valve in removed_valves:
            vids2fail.append(removed_valve.vid)
    
    vids = valve_register.vid2v.keys()
    remained_vids = list(set(vids)-set(vids2fail))

    return vids2fail,remained_vids

def generate_vids2fail(vids,fail_rate):
    num_failed_valves = int(fail_rate*len(vids))
    rand_fvids = list(np.random.choice(vids, num_failed_valves, replace=False))
    return rand_fvids

def get_simulation_results(reports):
    ave_num_segments = []
    ave_seg_pipe_size = []
    ave_max_pipe_seg = []
    for report in reports:
        stat = report.get_segments_stats()
        ave_num_segments.append(stat.num_multi_pipe_seg)
        ave_seg_pipe_size.append(np.mean(stat.seg_sizes_mean))
        ave_max_pipe_seg.append(np.mean(stat.seg_sizes_max))
    return ave_num_segments,ave_seg_pipe_size,ave_max_pipe_seg

def get_simulation_results(reports):
    ave_num_segments = []
    ave_seg_pipe_size = []
    ave_max_pipe_seg = []
    for report in reports:
        stat = report.get_segments_stats()
        ave_num_segments.append(stat.num_multi_pipe_seg)
        ave_seg_pipe_size.append(np.mean(stat.seg_sizes_mean))
        ave_max_pipe_seg.append(np.mean(stat.seg_sizes_max))
    return ave_num_segments,ave_seg_pipe_size,ave_max_pipe_seg
        
        
    

