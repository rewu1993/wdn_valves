import numpy as np
import copy

class Valve(object):
    def __init__(self,vid,nid,pid):
        self.vid = vid
        self.nid = nid
        self.pid = pid
        self.fail = True
        self.keep_open = True
        self.keep_closed = False
    def __str__(self):  
        return "valve with vid %d, links to nid %d and pid %d, fail status %d " % (
            self.vid, self.nid,self.pid,self.fail)
    

class ValveRegister(object):
    def __init__(self):  
        self.vid2v = {}
        self.nid2v = {}
        self.pid2v = {}
        self.nidpid2v = {}
        self.vids2open = []
        self.vids2close = []
        
    def recover_valves(self):
        for vid,valve in self.vid2v.items():
            if not (valve.keep_open or valve.keep_closed): 
                valve.fail = False
                
    def register(self,valves):
        for valve in valves:
            self.vid2v[valve.vid] = valve
            self.nidpid2v[(valve.nid,valve.pid)] = valve
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
    def __init__(self,valve_register,valid_nidpids,fixed_nidpids = []):
        self.vreg = copy.deepcopy(valve_register)
        self.valid_valves = self._init_valid_valves(valid_nidpids)
        self.normal_valves = self._init_valid_valves(valid_nidpids)
        self.fixed_valves = self._init_fixed_valves(fixed_nidpids)
        self.failed_valves = []

    def _init_valid_valves(self,valid_nidpids):
        valid_valves = []
        for nid, pid in valid_nidpids:
            valve = self.vreg.nidpid2v[(nid, pid)]
            valve.keep_open = False
            valve.fail = False
            valid_valves.append(valve)
        return valid_valves
    
    def _init_fixed_valves(self,fixed_nidpids):
        fixed_valves = []
        for nid, pid in fixed_nidpids:
            valve = self.vreg.nidpid2v[(nid, pid)]
            valve.keep_closed = True
            valve.fail = False
            fixed_valves.append(valve)
        return fixed_valves
        
    def fail_valve(self,vindex):
        valve = self.normal_valves.pop(vindex)
        valve.fail = True
        return valve
            
    def get_valve_dict(self):
        return self.vreg.vid2v
    
    def fail_valves(self,nv2fail):
        np.random.seed()
#         self.prev_state = copy.deepcopy(self)
        failed_valves = []
        for _ in range(nv2fail):
            vidx_pool = list(range(len(self.normal_valves)))
            vidx2fail = np.random.choice(vidx_pool,1,replace=False)[0]
            failed_valve = self.fail_valve(vidx2fail)
            failed_valves.append(failed_valve)
        self.failed_valves += failed_valves
        return failed_valves
    
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

def create_valvereg(lid2npair):
    valves = create_valves(lid2npair)
    vreg = ValveRegister()
    vreg.register(valves)
    return vreg

def create_valvestates(lid2npair,valid_nidpids,fixed_nidpids = []):
    vreg = create_valvereg(lid2npair)
    vstates = ValveStates(vreg,valid_nidpids,fixed_nidpids)
    return vstates


def get_N_nidpids(valve_register):
    nidpids = []
    for nid, valves in valve_register.nid2v.items():
        for v in valves:
            nidpids.append((v.nid,v.pid))
    return nidpids

    
def get_N1_nidpids(valve_register):
    nidpids = []
    for nid, valves in valve_register.nid2v.items():
        num_valves = len(valves)-1
        if num_valves > 0:
            valid_valves = np.random.choice(valves, num_valves, replace=False)
            for v in valid_valves:
                nidpids.append((v.nid,v.pid))
    return nidpids


def get_pipe_nidpids(valve_register):
    nidpids = []
    for nid, valves in valve_register.pid2v.items():
        num_valves = len(valves)-1
        if num_valves > 0:
            valid_valves = np.random.choice(valves, num_valves, replace=False)
            for v in valid_valves:
                nidpids.append((v.nid,v.pid))
    return nidpids



        