import math
import scipy
from scripts.segment_simulation import *

def asemble_adj_pids(pids):
    rows = []
    cols = []
    vals = []
    
    for i in range(len(pids)):
        for j in range(i+1,len(pids)):
            rows.append(pids[i])
            cols.append(pids[j])
            vals.append(1)
            
            rows.append(pids[j])
            cols.append(pids[i])
            vals.append(1)
    return rows,cols,vals
            
            
    
def assemble_pipe_adj_mtx(nid2lid):
    rows = []
    cols = []
    vals = []
    for nid, pids in nid2lid.items():
        r,c,v = asemble_adj_pids(pids)
        if len(r):
            assert(len(r) == math.factorial(len(pids))/math.factorial(len(pids)-2))
        rows+=r
        cols+=c
        vals+=v
    pipe_adj_mtx = scipy.sparse.csr_matrix((vals, (rows, cols)))
    return pipe_adj_mtx

def get_nxtlevel_pids(currlevel_pids,pipe_adj_mtx,black_list):
    nxt_pids = []
    for pid in currlevel_pids:
        neighbor_pids =  pipe_adj_mtx.getrow(pid).nonzero()[1]
        nxt_pids += list(neighbor_pids)
        
    nxt_pids_new = []
    for pid in nxt_pids:
        if (pid not in black_list) and (pid not in nxt_pids_new):
            nxt_pids_new.append(pid)
    return nxt_pids_new
        
def get_neighbor_pids(search_pid,pipe_adj_mtx,required_num,black_list):
    if required_num ==0:
        return []
    remained_num = required_num
    selected_pids = []
    curr_pids = [search_pid]
    while (remained_num > 0):
        nxt_level_pids = get_nxtlevel_pids(curr_pids,pipe_adj_mtx,black_list)
        if len(nxt_level_pids) > remained_num:
            selected_pids += list(np.random.choice(nxt_level_pids,remained_num,replace = False))
        else:
            selected_pids += nxt_level_pids
        curr_pids = nxt_level_pids
        remained_num = required_num-len(selected_pids)
        black_list += selected_pids
    return selected_pids

def extract_nids(pids,lid2nids):
    nids = []
    for pid in pids:
        nid1,nid2 = lid2nids[pid]
        nids.append(nid1)
        nids.append(nid2)
    return nids
        
def get_bundles(valid_pids,pipe_adj_mtx,
                required_num,source_pids,
                lid2nids,lid2lname,nid2nname):
    pipe_bundles,node_bundles = [],[]
    neighber_num = required_num-1
    for pid in valid_pids:
        black_list = copy.deepcopy(source_pids)
        pids_cluster = get_neighbor_pids(pid,pipe_adj_mtx,
                                         neighber_num,black_list)+[pid]
        nids_cluster = extract_nids(pids_cluster,lid2nids)    
        pnames_cluster = [lid2lname[pid] for pid in pids_cluster]
        nnames_cluster = [nid2nname[nid] for nid in nids_cluster]
        pipe_bundles.append(pnames_cluster)
        node_bundles.append(nnames_cluster)
    return pipe_bundles,node_bundles

def get_bundles_segments(segments,lid2lname,nid2nname):
    pipe_bundles,node_bundles = [], []
    for seg in segments:
        pnames = [lid2lname[pid] for pid in seg.pids]
        nnames = [nid2nname[nid] for nid in seg.nids]
        pipe_bundles.append(pnames)
        node_bundles.append(nnames)
    return pipe_bundles,node_bundles



def get_isolations_impact(pipe_bundles,node_bundles,sim_results,init_result,mode,lname2lid,nname2nid,lid2nids):
    assert(mode in ['demand','pressure'])
    impacts = []
    for pipe_bundle, node_bundle,sim_result in zip(pipe_bundles,node_bundles,sim_results):
        impact = find_isolation_impact(lname2lid,nname2nid,lid2nids,pipe_bundle,node_bundle,init_result,sim_result,mode)
        impacts.append(impact)
    return impacts

def find_isolation_impact(lname2lid,nname2nid,lid2nids,pipe_bundle, node_bundle,init_result,sim_result, mode, thre = 0.1):
    lose = {}
    nids = [nname2nid[nname] for nname in node_bundle]
    pids = [lname2lid[pname] for pname in pipe_bundle]
    related_nids = extract_nids(pids,lid2nids)

    init_val = init_result.node[mode].to_numpy().flatten()
    sim_val = sim_result.node[mode].to_numpy().flatten()
    average_direct_loss = sum(init_val[related_nids])/len(related_nids)
    lose['direct_loss'] = average_direct_loss*len(pids)
    
    val_diff = abs(init_val-sim_val)
    val_diff[nids] = 0  
    val_diff_ratio = val_diff/init_val*100
    valid_drop = val_diff[val_diff_ratio>thre]
    lose['indirect_loss'] = sum(valid_drop)
    lose['num_impacted_nodes'] = len(valid_drop)
    return lose

def bundle_hyrau_sims(wn,pipe_bundles,node_bundles,init_result):
    pool = mp.Pool(mp.cpu_count()-1)
    results = pool.starmap(isolate_pipes, [(pipe_name,node_name,wn,init_result) for pipe_name,node_name 
                                           in zip(pipe_bundles,node_bundles)])
    pool.close()
    pool.join()
    remove_temps()
    return results

def bundle_analysis(wn,pipe_bundles,node_bundles,lname2lid,nname2nid,lid2nids,mode = 'demand'):
    assert(wn.options.hydraulic.demand_model=='PDA')
    sim = wntr.sim.EpanetSimulator(wn)
    rand_name = './temp/'+str(np.random.randint(1e6))
    init_result = sim.run_sim(file_prefix=rand_name)
    
    hydrau_results = bundle_hyrau_sims(wn,pipe_bundles,node_bundles,init_result)
    impacts = get_isolations_impact(pipe_bundles,node_bundles,hydrau_results,
                                       init_result,mode,lname2lid,nname2nid,lid2nids)

    return impacts


    
    
    
    
    