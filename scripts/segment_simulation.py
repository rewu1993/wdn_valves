import os
import glob 
import multiprocessing as mp
import copy
import wntr
from scripts.valves import ValveStates,create_valvestates
from scripts.segment import *
from scripts.valves import *

def close_pipes(pipe_names,wn):
    for pipe_name in pipe_names:
        pipe = wn.get_link(pipe_name)        
        pipe.status = wntr.network.LinkStatus.Closed
    return wn

def open_pipes(pipe_names,wn):
    for pipe_name in pipe_names:
        pipe = wn.get_link(pipe_name)        
        pipe.status = wntr.network.LinkStatus.Open
    return wn

def remove_demand(node_names,wn):
    demands = []
    for node_name in node_names:
        demand = copy.deepcopy(wn.get_node(node_name).demand_timeseries_list[0].base_value)
        demands.append(demand)
        wn.get_node(node_name).demand_timeseries_list[0].base_value = 0
    return demands,wn

def restore_demand(node_names,demands,wn):
    for node_name,demand in zip(node_names,demands):
        wn.get_node(node_name).demand_timeseries_list[0].base_value = demand
    return wn
    
def isolate_pipes(pipe_names,node_names,wn,init_result):
    wn = copy.deepcopy(wn)
    wn = close_pipes(pipe_names,wn)
    demands, wn = remove_demand(node_names,wn)
    sim = wntr.sim.EpanetSimulator(wn)
    
    np.random.seed()
    rand_name = './temp/'+str(np.random.randint(1e9))
    try:
        results = sim.run_sim(file_prefix=rand_name)
    except:
        print ('Issues when running hydrualic simulation, use the initial result')
        results = init_result
    wn = open_pipes(pipe_names,wn)
    wn = restore_demand(node_names,demands,wn)
    return results

def remove_temps():
    temp_files = glob.glob("./temp/*")
    for file in temp_files:
        os.remove(file)
        
def hydrau_segments_sim(valid_segments):
    segment_pnames = get_segment_pnames(valid_segments)
    segment_nnames = get_segment_nnames(valid_segments)
    pool = mp.Pool(mp.cpu_count()-1)
    results = pool.starmap(isolate_pipes, [(pipe_name,node_name,wn) for pipe_name,node_name 
                                           in zip(segment_pnames,segment_nnames)])
    pool.close()
    remove_temps()
    return results
    
    
def find_direct_loses(valid_segments,init_demand):
    direct_loses = []
    for segment in valid_segments:
        direct_lose = []
        for nid in segment.nids:
            nname = nid2nname[nid]
            demand = init_demand[nname].to_numpy()[0]
            direct_lose.append ((nname,max(demand,0)))
        direct_loses.append(direct_lose)
    return direct_loses

def analyze_drop_ratio(dvals,init_vals,keys,thre = -0.1):
    drop_cond = dvals < thre
    drop_ratio = abs(dvals[drop_cond]/init_vals[drop_cond])*100
    impacted_keys = keys[drop_cond]
    drops = [(key,drop) for key, drop in zip(impacted_keys,drop_ratio)]
    return drops

def analyze_drop(dvals,init_vals,keys,thre = -0.1):
    drop_cond = dvals < thre
    drops = abs(dvals[drop_cond])
    impacted_keys = keys[drop_cond]
    drops = [(key,drop) for key, drop in zip(impacted_keys,drops)]
    return drops

def find_hydrau_loses(init_result,hydrau_results):
    init_pressure = init_result.node['pressure'].to_numpy().flatten()
    init_demand = init_result.node['demand'].to_numpy().flatten()
    keys = init_result.node['pressure'].keys().to_numpy().flatten()
    pressure_loses,demand_loses = [],[]
    
    for res in hydrau_results:
        pressure = res.node['pressure'].to_numpy().flatten()
        demand = res.node['demand'].to_numpy().flatten()
        pressure = [p if p >0 else 0 for p in pressure]
        demand = [d if d >0 else 0 for d in demand]
        dp = pressure-init_pressure
        pressure_drop = analyze_drop(dp,init_pressure,keys)
        pressure_loses.append(pressure_drop)

        dd = demand-init_demand
        demand_drop = analyze_drop(dd,init_demand,keys,-1e-6)
        demand_loses.append(demand_drop)
    return pressure_loses,demand_loses

def summarize_loses(loses):
    tot_lose = []
    for lose in loses:
        lose_sum = 0
        if len(lose):
            for k,l in lose:
                lose_sum+=l
        tot_lose.append(lose_sum)
    return tot_lose

def init_costs(wn):
    pname2pcost = {}
    pname2dcost = {}
    for pipe_name in wn.pipe_name_list:
        pname2pcost[pipe_name] = 0
        pname2dcost[pipe_name] = 0
    return pname2pcost,pname2dcost
    
    
def update_cost(pressure_costs,demand_costs,valid_segments,
               pname2pcost,pname2dcost):
    for i in range(len(valid_segments)):
        segment = valid_segments[i]
        pressure_cost = pressure_costs[i]
        demand_cost = demand_costs[i]
        for pid in segment.pids:
            pname = lid2lname[pid]
            pname2pcost[pname] += pressure_cost
            pname2dcost[pname] += demand_cost
    return pname2pcost,pname2dcost


        