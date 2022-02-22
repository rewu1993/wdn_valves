from scripts.utils import * 
from scripts.bundle_analysis import * 

def update_impact_dict(segment_impact_dict,pids_list,seg_impacts):
    for pids,seg_impact in zip(pids_list,seg_impacts):
        pid_keys = tuple(sorted(pids))
        segment_impact_dict[pid_keys] = seg_impact
    return segment_impact_dict

def calculate_damage_impact(wn,lid2lname,nid2nname,lname2lid,nname2nid,lid2nids,
                            num_valve2fail,valid_nidpids,src_pids,src_nids,pid2pcost,
                            segment_impact_dict,fixed_nidpids = [],
                           ):
    vstate = create_valvestates(lid2nids,valid_nidpids,fixed_nidpids)
    segnet_damage = HydroSegmentNet(vstate,src_pids,pid2pcost)
#     print (f'valves to break: {num_valve2fail}')
    for i in range(num_valve2fail):
        segnet_damage.valve_fail()
        
    new_segs = []
    old_impacts = []
    for seg in segnet_damage.valid_pipe_segments:
        if (set(src_nids).intersection(seg.nids)):
            print ('isolating the source!')
            return -1 # should not happen
        if len(seg.pids)>0 :
            pid_keys = tuple(sorted(seg.pids))
            if pid_keys not in segment_impact_dict:
                new_segs.append(seg)
            else:
                old_impacts.append(segment_impact_dict[pid_keys])

    updated_pipe_bundles,updated_node_bundles = get_bundles_segments(new_segs,lid2lname,nid2nname)
    print (f'number of segment to simulate: {len(updated_pipe_bundles)}')
    

    
    impact_updated = bundle_analysis(wn,updated_pipe_bundles,updated_node_bundles,lname2lid,nname2nid,lid2nids)
    pids_list = [seg.pids for seg in new_segs]
    damage_seg_impacts = get_segment_impacts(wn,pids_list,impact_updated,lid2lname)
    segment_impact_dict = update_impact_dict(segment_impact_dict,pids_list,damage_seg_impacts)
    
    
    tot_seg_impacts = damage_seg_impacts+old_impacts
    indirect_loss = calc_indirect_impact(tot_seg_impacts)
    direct_loss = calc_direct_impact(tot_seg_impacts)
    tot_loss = indirect_loss+direct_loss
    return (direct_loss,indirect_loss,tot_loss)


def mc_damage_assessment(wn,lid2lname,nid2nname,lname2lid,nname2nid,lid2nids,src_pids,src_nids,pid2pcost,
                         num_valve2fail,valid_nidpids,init_segment_impact_dict,
                         fixed_nidpids,num_steps):
    impact_list = []
    # warm up 
    for i in range(num_steps):
#         try: 
        impact = calculate_damage_impact(wn,lid2lname,nid2nname,lname2lid,nname2nid,lid2nids,
                                         num_valve2fail,valid_nidpids,src_pids,src_nids,pid2pcost,
                                             init_segment_impact_dict,fixed_nidpids)
        impact_list.append(impact)
#         except: 
#             print (Exception)
#             print ('fail to sim')
    save_impact_dict(init_segment_impact_dict)
    return impact_list

def evaluate_damages(wn,lid2lname,nid2nname,lname2lid,nname2nid,lid2nids,
                     src_pids,src_nids,pid2pcost,
                     impact_dict,valid_nidpids,
                     fail_rates,fixed_nidpids,
                     num_steps = 100,save_path = './data/result_demand.txt'):
    damage_lists = []
    for fail_rate in fail_rates:
        num_valve2fail = int((len(valid_nidpids))*fail_rate)
        damage_list = mc_damage_assessment(wn,lid2lname,nid2nname,lname2lid,nname2nid,lid2nids,src_pids,src_nids,pid2pcost,
                                           num_valve2fail,valid_nidpids,
                                           impact_dict,fixed_nidpids,
                                           num_steps)
        damage_lists.append(damage_list)
        save_progress(damage_lists,save_path)
    return damage_lists