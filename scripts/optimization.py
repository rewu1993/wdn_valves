import pickle
from scripts.utils import * 
from scripts.bundle_analysis import * 

def calculate_merge_impact(seg1,seg2,wn,segment_impact_dict,lid2lname,nid2nname,lname2lid,nname2nid,lid2nids,mode = 'demand'):
    merged_pids = seg1.pids + seg2.pids
    merged_pnames = [lid2lname[pid] for pid in merged_pids]
    
    merged_nids = seg1.nids + seg2.nids
    merged_nnames = [nid2nname[nid] for nid in merged_nids]

    merge_impact = bundle_analysis(wn,[merged_pnames],[merged_nnames],lname2lid,nname2nid,lid2nids)
    seg_impact = SegImpact(len(merged_pids),get_tot_length(wn),merge_impact)
    
    segment_impact_dict[tuple(sorted(merged_pids))] = seg_impact
    return seg_impact


def init_remove_impacts(wn,segnet,segment_impact_dict,lid2lname,nid2nname,lname2lid,nname2nid,lid2nids,mode = 'demand'):
    pnames_list = []
    nnames_list = []
    pids_list = []
    
    for segment in segnet.valid_pipe_segments:
        pids = segment.pids
        pnames =  [lid2lname[pid] for pid in pids]
        pnames_list.append(pnames)
        pids_list.append(pids)
        
        nids = segment.nids
        nnames = [nid2nname[nid] for nid in nids]
        nnames_list.append(nnames)
    
    impacts = bundle_analysis(wn,pnames_list,nnames_list,lname2lid,nname2nid,lid2nids)
    seg_impacts = get_segment_impacts(wn,pids_list,impacts,lid2lname)
    segment_impact_dict = update_impact_dict(segment_impact_dict,pids_list,seg_impacts)
    return seg_impacts

def get_merged_properties(seg1,seg2,lid2lname,nid2nname):
    merged_pids = seg1.pids + seg2.pids
    merged_nids = seg1.nids + seg2.nids
    merged_pnames = [lid2lname[pid] for pid in merged_pids]
    merged_nnames = [nid2nname[nid] for nid in merged_nids]
    return merged_pnames,merged_nnames
    

def init_merge_impacts(wn,valves,segnet,segment_impact_dict,lid2lname,nid2nname,lname2lid,nname2nid,lid2nids,mode = 'demand'):
    pnames_list = []
    nnames_list = []
    pids_list = []
    for valve in valves:
        seg_from = segnet.nid2seg[valve.nid]
        seg_to = segnet.pid2seg[valve.pid]
        merged_pnames,merged_nnames = get_merged_properties(seg_from,seg_to,lid2lname,nid2nname)

        pnames_list.append(merged_pnames)
        nnames_list.append(merged_nnames)
        
        pids = seg_from.pids + seg_to.pids
        pids_list.append(pids)
    
    impacts = bundle_analysis(wn,pnames_list,nnames_list,lname2lid,nname2nid,lid2nids)
    seg_impacts = get_segment_impacts(wn,pids_list,impacts,lid2lname)
    segment_impact_dict = update_impact_dict(segment_impact_dict,pids_list,seg_impacts)
    return seg_impacts    
    


def get_merge_seg_impact(seg1,seg2,segment_impact_dict):
    pids = seg1.pids + seg2.pids 
    k = tuple(sorted(pids))
    impact = segment_impact_dict[k]
    return impact
    

def get_seg_impact(segment,segment_impact_dict):
    if len(segment.pids) == 0:
#         print ('node segment')
        impact = SegImpact(0,1,{'direct_loss':0,
                             'indirect_loss':0})
    else:
        k = tuple(sorted(segment.pids))
        impact = segment_impact_dict[k]
    return impact

def find_valve2remove(segnet,segment_impact_dict):
    min_loss,min_valve = 1e10,None
    min_direct_loss,min_indirect_loss = None, None
    for i, valve in enumerate(segnet.vstates.normal_valves):
        if valve in segnet.vstates.fixed_valves:
            continue
        seg_from = segnet.nid2seg[valve.nid]
        seg_to = segnet.pid2seg[valve.pid]
        impact1 = get_seg_impact(seg_from,segment_impact_dict)
        impact2 = get_seg_impact(seg_to,segment_impact_dict)
        impact3 = get_merge_seg_impact(seg_from,seg_to,segment_impact_dict)

        cost_term = abs(impact1.prob*(impact3.tot_loss-impact1.tot_loss)+
                     impact2.prob*(impact3.tot_loss-impact2.tot_loss))
        if min_loss > cost_term:
            min_loss =  cost_term
            min_valve = valve
            min_direct_loss = abs(impact1.prob*(impact3.direct_loss-impact1.direct_loss)+
                     impact2.prob*(impact3.direct_loss-impact2.direct_loss))
            min_indirect_loss = min_loss- min_direct_loss
            
    return min_valve,min_direct_loss,min_indirect_loss

def find_new_bundles(segnet,segment_impact_dict,lid2lname,nid2nname):
    pnames_list, nnames_list = [],[]
    pids_list = []
    for i, valve in enumerate(segnet.vstates.normal_valves):
        seg1 = segnet.nid2seg[valve.nid]
        seg2 = segnet.pid2seg[valve.pid]
        
        pids = seg1.pids + seg2.pids 
        nids = seg1.nids + seg2.nids
        k = tuple(sorted(pids))
        
        if k not in segment_impact_dict:
            pnames = [lid2lname[pid] for pid in pids]
            nnames = [nid2nname[nid] for nid in nids]
            pnames_list.append(pnames)
            nnames_list.append(nnames)
            pids_list.append(pids)
    return pnames_list,nnames_list,pids_list
            
        
def update_merging_status(wn,segnet,segment_impact_dict,lid2lname,nid2nname,lname2lid,nname2nid,lid2nids):
    pnames_list,nnames_list,pids_list = find_new_bundles(segnet,segment_impact_dict,lid2lname,nid2nname)
    print (f'updating {len(pnames_list)} segments')
    impacts = bundle_analysis(wn,pnames_list,nnames_list,lname2lid,nname2nid,lid2nids)
    seg_impacts = get_segment_impacts(wn,pids_list,impacts,lid2lname)
    segment_impact_dict = update_impact_dict(segment_impact_dict,pids_list,seg_impacts)
    return segment_impact_dict
    
def valve_optimal_removal(wn,segnet,segment_impact_dict,num_valve2remove,
                          lid2lname,nid2nname,lname2lid,nname2nid,lid2nids):
    cum_dirloss,cum_indirloss = [0], [0]
    for i in range(num_valve2remove):
        valve,dir_loss,indir_loss = find_valve2remove(segnet,segment_impact_dict)
        print (f'remove {i} valve with loss {dir_loss+indir_loss}')
        cum_dirloss.append(cum_dirloss[-1]+dir_loss)
        cum_indirloss.append(cum_indirloss[-1]+indir_loss)
        
        segnet.fail_valve(valve)
        segment_impact_dict = update_merging_status(wn,segnet,segment_impact_dict,
                                                    lid2lname,nid2nname,lname2lid,nname2nid,lid2nids)
    return segnet,cum_dirloss,cum_indirloss
        
        

        
    