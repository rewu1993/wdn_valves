import numpy as np
import copy

class Valve(object):
    def __init__(self,vid,nid,pid):
        self.vid = vid
        self.nid = nid
        self.pid = pid
        self.fail = False
        self.keep_open = False
        self.keep_closed = False
    def __str__(self):  
        return "valve with vid %d, links to nid %d and pid %d, fail status %d " % (
            self.vid, self.nid,self.pid,self.fail)
    

class ValveRegister(object):
    def __init__(self):  
        self.vid2v = {}
        self.nid2v = {}
        self.pid2v = {}
        self.vids2open = []
        self.vids2close = []
        
    def recover_valves(self):
        for vid,valve in self.vid2v.items():
            if not (valve.keep_open or valve.keep_closed): 
                valve.fail = False
                
    def register(self,valves):
        for valve in valves:
            self.vid2v[valve.vid] = valve
            if not (valve.nid in self.nid2v):
                self.nid2v[valve.nid] = []
            self.nid2v[valve.nid].append(valve)

            if not (valve.pid in self.pid2v):
                self.pid2v[valve.pid] = []
            self.pid2v[valve.pid].append(valve)
    
    def update_open_valves(self, vids2open):
        self.vids2open = vids2open
        for vid in vids2open:
            valve = self.vid2v[vid]
            valve.keep_open = True
            valve.fail = True
    
    def update_closed_valves(self,vids2close):
        self.vids2close = vids2close
        for vid in vids2close:
            valve = self.vid2v[vid]
            valve.keep_closed = True
            valve.fail = False
            
    @property        
    def topo_vids(self):
        return set(self.vids2open+self.vids2close)
    
    @property        
    def valid_vids(self):
        return list(set(self.vid2v.keys())-self.topo_vids)
            

class ValveStates(object):
    def __init__(self,valve_register,pids_white,N1 = False):
        self.vreg = copy.deepcopy(valve_register)
        self.white_valves = self._get_white_valves(pids_white)
        self.topo_valves = self._get_topo_valves(N1)
        self.valid_valves = self._init_valid_valves()
        
        self.normal_valves = self._init_valid_valves()
        self.failed_valves = []
#         self.prev_state = None

    def _get_white_valves(self,pids_white):
        white_valves = []
        for white_pid in pids_white:
            valves = self.vreg.pid2v[white_pid]
            for v in valves:
                v.keep_closed = True
                v.fail = False
                white_valves.append(v)
        return white_valves

    def _adjust2N_1(self):
        adjust_valves = []
        for nid, valves in self.vreg.nid2v.items():
            topo_valve = np.random.choice(valves, 1, replace=False)[0]
            if topo_valve.keep_closed == False:
                topo_valve.keep_open = True
                topo_valve.fail = True
                adjust_valves.append(topo_valve)
        return adjust_valves
    
    def _get_topo_valves(self,N1):
        topo_valves = []
        if N1:
            n1_valves = self._adjust2N_1()
            topo_valves += n1_valves
        return topo_valves
    
    def _init_valid_valves(self):
        valid_valves = []
        for vid, valve in self.vreg.vid2v.items():
            if valve not in self.topo_valves:
                if valve not in self.white_valves:
                    valid_valves.append(valve)
        return valid_valves
    
    def _fail_valve(self,vindex):
        valve = self.normal_valves.pop(vindex)
        valve.fail = True
        return valve
    
    def fail_valves(self,nv2fail):
        np.random.seed()
#         self.prev_state = copy.deepcopy(self)
        failed_valves = []
        for _ in range(nv2fail):
            vidx_pool = list(range(len(self.normal_valves)))
            vidx2fail = np.random.choice(vidx_pool,1,replace=False)[0]
            failed_valve = self._fail_valve(vidx2fail)
            failed_valves.append(failed_valve)
        self.failed_valves += failed_valves
        return failed_valves
    
#     def roll_back(self):
#         self.vreg = self.prev_state.vreg
#         self.topo_valves = self.prev_state.topo_valves
#         self.normal_valves = self.prev_state.normal_valves
#         self.prev_state = self.prev_state.prev_state
        
    def get_valve_dict(self):
        return self.vreg.vid2v
    
#     def fail_all_valid_valves(self):
#         self.prev_state = copy.deepcopy(self)
#         for valid_valve in self.valid_valves:
#             valid_valve.fail = True
            
    @property
    def fail_rate(self):
        return 1-len(self.normal_valves)/len(self.valid_valves)
    
def create_valves(lid2npair):
    vid = 0
    valves = []
    for lid, npairs in lid2npair.items():
        for nid in npairs:
            v = Valve(vid,nid,lid)
            vid += 1
            valves.append(v)
    return valves

def create_valvestates(lid2npair,src_nids,N1):
    valves = create_valves(lid2npair)
    vreg = ValveRegister()
    vreg.register(valves)
    vstates = ValveStates(vreg,src_nids,N1)
    return vstates
        
        