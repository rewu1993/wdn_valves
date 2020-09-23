from scripts.mesh import *
from scripts.simulation import *
from scripts.graph import *

def get_bfs_levels(mesh):
    fail_rate = 1
    valve_register = mesh.valve_register
    
    valve_register.recover_valves()
    vids2fail = generate_vids2fail(mesh.valid_vids,fail_rate)
    valves_dict = fail_valves(valve_register.vid2v,vids2fail)
    A = assemble_adjacency_mtx(mesh.grid_size,valves_dict)
    valve_register.recover_valves()
    
    return bfs_levels(0,A)

def get_nids2maintain(bfs_levels, level):
    nids = []
    for i in range(level):
        idx = 2*(i+1)
        nids+=bfs_levels[idx]
    return nids

def get_vids2maintain(nids2maintain,nid2v):
    vids = []
    for nid in nids2maintain:
        valves = nid2v[nid]
        for v in valves:
            if not (v.keep_open or v.keep_closed):
                vids.append(v.vid)
    return vids  

def maintain_valves(mesh,maintain_level):
    levels = get_bfs_levels(mesh)
    nids = get_nids2maintain(levels,maintain_level)
    valve_reg = mesh.valve_register
    vids = get_vids2maintain(nids,valve_reg.nid2v)
    return vids

def create_segsum(mesh,valves_dict):
    segments = simulate_segments(mesh.grid_size,valves_dict)
    mtx_diff = create_mtx_diff(mesh.grid_size,valves_dict,mesh.valid_vids)
    num_closed_pipes = len(mesh.get_closed_pids())
    num_nodes = mesh.grid_size*mesh.grid_size
    seg_sum = SegmentSummary(num_nodes,segments,mtx_diff,num_closed_pipes)
    return seg_sum
    
def generate_seg_sum_maintain(mesh,vfail_rate,degree):
    valve_register = mesh.valve_register
    valve_register.recover_valves()
    
    vids2maintain = maintain_valves(mesh,degree)
    normal_vids = list(set(mesh.valid_vids)-set(vids2maintain))
    
    maintain2fail  = generate_vids2fail(vids2maintain,vfail_rate/5)
    others2fail = generate_vids2fail(normal_vids,vfail_rate)
    vids2fail = maintain2fail+others2fail
    
    valves_dict = fail_valves(valve_register.vid2v,vids2fail)
    
    seg_sum = create_segsum(mesh,valves_dict)
    return seg_sum

def repair_impact(mesh,fail_rate,valid_pids,maintain_degree,repair_degree):
    seg_sum = generate_seg_sum_maintain(mesh,fail_rate,maintain_degree)
    return seg_sum.multi_pipe_iso_consequences(valid_pids,repair_degree)

def mc_repair_impact(mesh,fail_rate,valid_pids,maintain_degree,repair_degree,num_sim = 100):
    pool = mp.Pool(mp.cpu_count()-1)
    results = pool.starmap(repair_impact, [(mesh,fail_rate,valid_pids,maintain_degree,repair_degree) for _ in range(num_sim)])
    pool.close()
    
    directs,unintends = [],[]
    for direct,unintend in results:
        directs.append(direct)
        unintends.append(unintend)
        
    return np.mean(directs)/len(valid_pids),np.mean(unintends)/len(valid_pids)

def calculate_consequence(mesh,maintain_degrees, repair_degree,fail_rate):
    directs, unintends = [],[]
    maintain_ratio = []
    for maintain_degree in maintain_degrees:
        vids2maintain = maintain_valves(mesh,maintain_degree)
        num_valves = len(vids2maintain)
        ratio = num_valves/len(mesh.valid_vids)
        maintain_ratio.append(ratio)
    
        direct,unintend = mc_repair_impact(mesh,fail_rate,mesh.valid_pids,
                                       maintain_degree,repair_degree,num_sim = 60)
        directs.append(direct)
        unintends.append(unintend)
    return directs,unintends,maintain_ratio

def analyze_consequence(consequence):
    directs,unintends,maintain_ratio = consequence
    direct_base,unintend_base = directs[0],unintends[0]
    reductions_direct,reductions_unintend = [], []
    for direct, unintend in zip(directs,unintends):
        tot = direct+unintend
        rd_direct = direct_base-direct
        rd_unintend = (unintend_base- unintend)/tot        
        reductions_direct.append(rd_direct)
        reductions_unintend.append(rd_unintend)
    return np.array(maintain_ratio),np.array(reductions_unintend)
        
    