import numpy as np 
import pickle
import pandas as pd

class SegImpact(object):
    def __init__(self,length,tot_length,sim_impact):
        self.length = length
        self.prob = length/tot_length
#         self.prob = num_pipes/3029
        self.direct_loss = sim_impact['direct_loss']
        self.indirect_loss = sim_impact['indirect_loss']
        self.tot_loss = self.direct_loss+self.indirect_loss
        self.norm_loss = self.tot_loss*self.prob 
        self.norm_direct_loss = self.direct_loss*self.prob 
        self.norm_indirect_loss = self.indirect_loss*self.prob 
        
def extract_nids(pids):
    nids = []
    for pid in pids:
        nid1,nid2 = lid2nids[pid]
        nids.append(nid1)
        nids.append(nid2)
    return nids

def get_segment_length(wn,pids,lid2lname):
    length = 0
    for pid in pids:
        pname = lid2lname[pid]
        pipe = wn.get_link(pname)
        length += pipe.length
    return length

def get_segment_impacts(wn,pids_list,impacts,lid2lname):
    seg_impacts = []
    for i, impact in enumerate(impacts):
        pids = pids_list[i]
        l = get_segment_length(wn,pids,lid2lname)
        seg_impact = SegImpact(l,get_tot_length(wn),impact)
        seg_impacts.append(seg_impact)
    return seg_impacts

def update_impact_dict(segment_impact_dict,pids_list,seg_impacts):
    for pids,seg_impact in zip(pids_list,seg_impacts):
        pid_keys = tuple(sorted(pids))
        segment_impact_dict[pid_keys] = seg_impact
    return segment_impact_dict


def save_impact_dict(impact_dict,file_path ="./data/opt_impact_dict_rh.txt"):
    with open(file_path, "wb") as fp:   #Pickling
          pickle.dump(impact_dict, fp,
                      protocol=pickle.HIGHEST_PROTOCOL)
    print ('dict saved')
            
def read_impact_dict(file_path ="./data/opt_impact_dict_rh.txt" ):
    with open(file_path, "rb") as fp:   # Unpickling
        impact_dict = pickle.load(fp)
    return impact_dict
    
def save_progress(result,file_path ="./data/result_rh.txt"):
    with open(file_path, "wb") as fp:   #Pickling
          pickle.dump(result, fp,
                      protocol=pickle.HIGHEST_PROTOCOL)
    print ('result saved')
    
    
    
        
        
def get_tot_length(wn):
    tot_length = 0
    for pipe_name in wn.pipe_name_list:
        pipe = wn.get_link(pipe_name)  
        tot_length += pipe.length
    return tot_length


# map demand to pipes 
def m3togal(m):
    return 264.172*m 


def extract_nids(pids):
    nids = []
    for pid in pids:
        nid1,nid2 = lid2nids[pid]
        nids.append(nid1)
        nids.append(nid2)
    return nids
    
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
        
            
def get_valid_segments(segnet,src_nids):
    valid_segs = []
    for segment in segnet.segments:
        if src_nid not in segment.nids:
            if len(segment.pids) > 0:
                valid_segs.append(segment)
    return valid_segs
    
def get_segment_pnames(valid_segs):
    segment_pnames = []
    for segment in valid_segs:
        pids = segment.pids
        pnames = [lid2lname[pid] for pid in pids]
        segment_pnames.append(pnames)
    return segment_pnames

def get_segment_nnames(valid_segs):
    segment_nnames = []
    for segment in valid_segs:
        nids = segment.nids
        nnames = [nid2nname[nid] for nid in nids]
        segment_nnames.append(nnames)
    return segment_nnames


def get_seg_impact(segment,segment_impact_dict):
    if len(segment.pids) == 0:
#         print ('node segment')
        impact = SegImpact(0,1,{'direct_loss':0,
                             'indirect_loss':0})
    else:
        k = tuple(sorted(segment.pids))
        impact = segment_impact_dict[k]
    return impact

def get_segment_sizes(segnet):
    sizes = []
    for seg in segnet.valid_pipe_segments:
        sizes.append(len(seg.pids))
    return sizes

def evaluate_network_risk(segnet,segment_impact_dict):
    direct_risk, indirect_risk = 0, 0
    for seg in segnet.valid_pipe_segments:
        impact = get_seg_impact(seg,segment_impact_dict)
        direct_risk += impact.direct_loss*impact.prob
        indirect_risk += impact.indirect_loss*impact.prob
    return m3togal(direct_risk)*60,m3togal(indirect_risk)*60


def get_loss(init_loss,cum_loss):
    loss = []
    for l in cum_loss:
        loss.append(m3togal(l)*60+init_loss)
    return np.array(loss)


def calc_tot_impact(seg_impacts):
    norm_loss = [seg_impact.norm_loss for seg_impact in seg_impacts]
    return sum(norm_loss)

def calc_direct_impact(seg_impacts):
    norm_loss = [seg_impact.norm_direct_loss for seg_impact in seg_impacts]
    return sum(norm_loss)

def calc_indirect_impact(seg_impacts):
    norm_loss = [seg_impact.norm_indirect_loss for seg_impact in seg_impacts]
    return sum(norm_loss)


def extract_hydrau_result(result):
    direct_losses,indirect_losses,tot_losses = [],[],[]
    for direct_loss,indirect_loss,tot_loss in result:
        direct_losses.append(direct_loss)
        indirect_losses.append(indirect_loss)
        tot_losses.append(tot_loss)
    return direct_losses,indirect_losses,tot_losses
        
def summarize2df(sim_result,fail_rates,vtype):
    direct_risks,indirect_risks,tot_risks = [],[],[]
    fail_rate_list = [] 

    # initial 
    for i,res in enumerate(sim_result):
        direct_losses,indirect_losses,tot_losses = extract_hydrau_result(res)
        fail_rate = fail_rates[i]
        
        direct_risks += [m3togal(d)*60 for d in direct_losses]
        indirect_risks += [m3togal(d)*60 for d in indirect_losses]
        tot_risks += [m3togal(d)*60 for d in tot_losses]
        
        fail_string = int(fail_rate*100)
        fail_rate_list += len(direct_losses)*[fail_string]

    df_dict = {'Direct Risk': direct_risks,
               'Indirect Risk': indirect_risks,
               'Tot Risk': tot_risks,
               'Fail Rate (%)':fail_rate_list,
               'Type': len(tot_risks)*[vtype]
    }
    df_risk = pd.DataFrame.from_dict(df_dict)
    return df_risk
    


    