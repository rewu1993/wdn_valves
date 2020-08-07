import numpy as np

class ValveRegister(object):
    def __init__(self):  
        self.vid2v = {}
        self.nid2v = {}
        self.pid2v = {}
    def recover_valves(self):
        for vid,valve in self.vid2v.items():
            valve.fail = False
            

class Valve(object):
    def __init__(self,vid,nid,pid):
        self.vid = vid
        self.nid = nid
        self.pid = pid
        self.fail = False
    def __str__(self):  
        return "valve with vid %d, links to nid %d and pid %d, fail status %d " % (
            self.vid, self.nid,self.pid,self.fail)
    
    
def register_valve(valve,valve_register):
    valve_register.vid2v[valve.vid] = valve
    
    if not (valve.nid in valve_register.nid2v):
        valve_register.nid2v[valve.nid] = []
    valve_register.nid2v[valve.nid].append(valve)
    
    if not (valve.pid in valve_register.pid2v):
        valve_register.pid2v[valve.pid] = []
    valve_register.pid2v[valve.pid].append(valve)
    
def register_valves(valves,valve_register):
    for valve in valves:
        register_valve(valve,valve_register)
        
