from enum import Enum
import numpy as np

class NodeType(Enum):
    NORMAL = 0
    LEFT = 1
    RIGHT = 2
    UP = 3
    DOWN = 4
    UPPER_LEFT = 5
    UPPER_RIGHT = 6
    LOWER_LEFT = 7
    LOWER_RIGHT = 8
    
class NodeTypeChecker(object):
    def __init__(self,grid_size):
        self.grid_size = grid_size
        self.left_bound_nids = np.array([i*grid_size for i in range(grid_size)])
        self.right_bound_nids = self.left_bound_nids + grid_size -1
        self.upper_bound_nids = np.array([i for i in range(grid_size)])
        self.lower_bound_nids = self.upper_bound_nids+(grid_size-1)*grid_size
        self.corners_nids = [self.left_bound_nids[0],self.left_bound_nids[-1],
                             self.right_bound_nids[0],self.right_bound_nids[-1]]
        
    def get_node_type(self, nid):
        if nid in self.corners_nids:
            return self._get_corner_nids(nid)
        if nid in self.left_bound_nids:
            return NodeType.LEFT
        elif nid in self.right_bound_nids:
            return NodeType.RIGHT
        elif nid in self.upper_bound_nids:
            return NodeType.UP
        elif nid in self.lower_bound_nids:
            return NodeType.DOWN
        else:
            return NodeType.NORMAL
        
        
    def _get_corner_nids(self,nid):
        for i in range(4):
            if nid == self.corners_nids[i]:
                corner = i
        if corner == 0 :
            return NodeType.UPPER_LEFT
        elif corner == 1:
            return NodeType.LOWER_LEFT
        elif corner == 2:
            return NodeType.UPPER_RIGHT
        elif corner == 3:
            return NodeType.LOWER_RIGHT
        
class NodeNeighbors(object):
    def __init__(self,nid,grid_size):
        self.left = nid-1
        self.right = nid+1
        self.up = nid-grid_size
        self.down = nid+grid_size
        

    def adjust_neighbors(self,valve_neighbors):
        if not valve_neighbors.left:
            self.left = None
        if not valve_neighbors.right:
            self.right = None
        if not valve_neighbors.down:
            self.down = None
        if not valve_neighbors.up:
            self.up = None
            
    def get_neighbors(self):
        return [self.left,self.right,self.up,self.down]
        
    def __str__(self):  
        return f"left: {self.left}, right: {self.right}, up {self.up}, down {self.down}"
            



class ValveNeighbors(object):
    def __init__(self,nid):
        self.nid = nid
        self.left = None
        self.right = None
        self.up = None
        self.down = None
        
    def adjust_neighbors(self,nid2valve,node_type):
        valves = nid2valve[self.nid]
        valves.sort(key=lambda x:x.vid)
        if node_type==NodeType.LEFT:
            self.right,self.up,self.down = valves
        elif node_type==NodeType.RIGHT:
            self.left,self.up,self.down = valves
        elif node_type==NodeType.UP:
            self.left,self.right,self.down = valves
        elif node_type==NodeType.DOWN:
            self.left,self.right,self.up = valves
        elif node_type==NodeType.UPPER_LEFT:
            self.right,self.down = valves
        elif node_type==NodeType.UPPER_RIGHT:
            self.left,self.down = valves
        elif node_type==NodeType.LOWER_LEFT:
            self.right,self.up = valves
        elif node_type==NodeType.LOWER_RIGHT:
            self.left,self.up = valves
        else:
            self.left,self.right,self.up,self.down = valves
            
    def get_neighbors(self):
        return [self.left,self.right,self.up,self.down]
    
    def __str__(self):  
        return f"left: {self.left}, right: {self.right}, up: {self.up}, down: {self.down}"
        
        
class Node(object):
    def __init__(self,nid,node_type_checker,grid_size):
        self.nid = nid
        self.node_type = node_type_checker.get_node_type(nid)
        self.node_neighbors = NodeNeighbors(nid,grid_size)
        self.valve_neighbors = ValveNeighbors(nid)
        self.pipe_neighbors = [None,None,None,None]
        self.closed_pipes = [False,False,False,False]
    
    def adjust_neighbors(self,nid2valve):
        self.valve_neighbors.adjust_neighbors(nid2valve,self.node_type)
        self.node_neighbors.adjust_neighbors(self.valve_neighbors)
        self.pipe_neighbors = self.create_pipe_neighbors()
    
    def create_pipe_neighbors(self):
        pipe_neighbors = [None,None,None,None]
        v_neighbors = self.get_valve_neighbors()
        for i,v in enumerate(v_neighbors):
            if v:
                pipe_neighbors[i] = v.pid
            else:
                self.closed_pipes[i] = True
        return pipe_neighbors
    
    def get_node_neighbor_ids(self):
        return self.node_neighbors.get_neighbors()
    
    def get_valve_neighbors(self):
        return self.valve_neighbors.get_neighbors()
    
    def get_pipe_neighbor_ids(self):
        return self.pipe_neighbors
    
    def degree(self):
        d = 0
        for pid in self.pipe_neighbors:
            if pid!=None: d+=1
        return d
        
        
    def __str__(self):  
        return f"nid: {self.nid}, ntype: {self.node_type},\
        nneighbors: {self.node_neighbors},\
        pneighbors: {self.pipe_neighbors},\
        vneighbors: {self.valve_neighbors},\
        degree: {self.degree()}" 

    
def get_nid2nodes(grid_size,nid2v_dict):
    nid2nodes = {}
    type_checker = NodeTypeChecker(grid_size)
    N = grid_size*grid_size
    for nid in range(N):
        node = Node(nid,type_checker,grid_size)
        node.adjust_neighbors(nid2v_dict)
        nid2nodes[nid] = node     
    return nid2nodes 
    