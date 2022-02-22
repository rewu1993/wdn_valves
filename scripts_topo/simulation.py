import numpy as np
import multiprocessing as mp
from scripts_topo.segment import * 


def fail_valves(valves_dict, vids2fail):
    for vid,v in valves_dict.items():
        if vid in vids2fail:
            v.fail = True
    return valves_dict 

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
    np.random.seed()
    vids = list(vids)
    num_failed_valves = int(fail_rate*len(vids))
    rand_fvids = list(np.random.choice(vids, num_failed_valves, replace=False))
    return rand_fvids

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
    

def simulate_segments(grid_size,valves_dict):
    A = assemble_adjacency_mtx(grid_size,valves_dict)
    segments = find_segments(A,grid_size*grid_size)
    return segments

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


def generate_sim_report_topo(valve_register,valid_vids,num_simulation,fail_rate):
    report = SegmentReport(grid_size)
    for i in range(num_simulation):
        valve_register.recover_valves()
        vids2fail = generate_vids2fail(valid_vids,fail_rate) 
        valves_dict = fail_valves(valve_register.vid2v,vids2fail)
        segments = simulate_segments(grid_size,valves_dict)
        report = update_segment_report(segments,report)
    return report

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


# def get_simulation_results(reports,trivial_pids = {}):
#     ave_num_segments = []
#     ave_seg_pipe_size = []
#     ave_max_pipe_seg = []
#     for report in reports:
#         stat = report.get_segments_stats(trivial_pids)
#         ave_num_segments.append(stat.num_multi_pipe_seg)
#         ave_seg_pipe_size.append(np.mean(stat.seg_sizes_mean))
#         ave_max_pipe_seg.append(np.mean(stat.seg_sizes_max))
#     return ave_num_segments,ave_seg_pipe_size,ave_max_pipe_seg


def get_vids2open(mesh):
    contraction_reg = mesh.contraction_reg
    vids2open = []
    for v1,v2 in contraction_reg.vpairs:
        vids2open.append(v1.vid)
        vids2open.append(v2.vid)
    return vids2open


def get_vids2close(mesh):
    vids2close = []
    for pid in mesh.closed_pids:
        v1,v2 = valve_register.pid2v[pid]
        vids2close.append(v1.vid)
        vids2close.append(v2.vid)
    return vids2close


'''
Segment summary part 
'''
def create_null_valves_dict(valves_dict,valid_vids):
    null_dict = valves_dict.copy()
    for vid,v in null_dict.items():
        if vid in valid_vids:
            v.fail = True
    return null_dict       

def create_mtx_diff(grid_size, valves_dict,valid_vids):
    A = assemble_adjacency_mtx(grid_size,valves_dict)
    null_valves = create_null_valves_dict(valves_dict,valid_vids)
    A_null = assemble_adjacency_mtx(grid_size,null_valves)
    A_diff = A_null - A
    return A_diff
    
def generate_seg_sum(mesh,vfail_rate):
    valve_register = mesh.valve_register
    valve_register.recover_valves()
    vids2fail = generate_vids2fail(mesh.valid_vids,vfail_rate)
    valves_dict = fail_valves(valve_register.vid2v,vids2fail)
    segments = simulate_segments(mesh.grid_size,valves_dict)
    mtx_diff = create_mtx_diff(mesh.grid_size,valves_dict,mesh.valid_vids)
    num_closed_pipes = len(mesh.get_closed_pids())
    num_nodes = mesh.grid_size*mesh.grid_size
    seg_sum = SegmentSummary(num_nodes,segments,mtx_diff,num_closed_pipes)
    return seg_sum
    
def iso_consequence(mesh,vfail_rate,pids2sim):
    seg_sum = generate_seg_sum(mesh,vfail_rate)
    return seg_sum.pipe_iso_consequences(pids2sim)

def mc_single_iso_consequence(mesh,vfail_rate,pids2sim,mc_num = 100):
    pool = mp.Pool(mp.cpu_count()-1)
    results = pool.starmap(iso_consequence, [(mesh,vfail_rate,pids2sim) for _ in range(mc_num)])
    pool.close()
    directs_sum,unintends_sum = np.zeros(len(pids2sim)),np.zeros(len(pids2sim))
    for direct,unintend in results:
        directs_sum += direct 
        unintends_sum += unintend
    return directs_sum/mc_num, unintends_sum/mc_num
    
def degree_impact(mesh,fail_rate,degree,valid_pids):
    seg_sum = generate_seg_sum(mesh,fail_rate)
    return seg_sum.multi_pipe_iso_consequences(valid_pids,degree)
    
def mc_degree_impact(mesh,fail_rate,degree,valid_pids,num_sim = 100):
    pool = mp.Pool(mp.cpu_count()-1)
    results = pool.starmap(degree_impact, [(mesh,fail_rate,degree,valid_pids) for _ in range(num_sim)])
    pool.close()
    
    directs,unintends = [],[]
    for direct,unintend in results:
        directs.append(direct)
        unintends.append(unintend)
        
    return np.mean(directs)/len(valid_pids),np.mean(unintends)/len(valid_pids)

def multi_degree_impact(mesh,fail_rate,degree_list):
    degree_result = []
    for degree in degree_list:
        results = mc_degree_impact(mesh,fail_rate,degree,mesh.valid_pids,30)
        degree_result.append(results)
    return degree_result
    
    
def multi_vpfail_simulation(mesh,fail_rates, degree_list):
    fail_results = []
    for fail_rate in fail_rates:
        print (f'Start simulating valve fail rate {fail_rate}')
        degree_result = multi_degree_impact(mesh,fail_rate,degree_list)
        fail_results.append(degree_result)
    return fail_results

def parse_directs_unintends(result):
    directs, unintends = [], []
    for direct,unintend in result:
        directs.append(direct)
        unintends.append(unintend)
    return directs,unintends

def generate_degree_ratio(degree, low, high = 1):
    if degree < 3:
        low = 1
    return np.random.uniform(low,high)
        



        