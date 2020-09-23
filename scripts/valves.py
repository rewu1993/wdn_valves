import numpy as np

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
            
        
            
