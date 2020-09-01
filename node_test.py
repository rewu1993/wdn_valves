from scripts.node import *
from scripts.grid import *
import unittest

class TestNodes(unittest.TestCase):
    def setUp(self):
        grid_size = 3
        valves = generate_valves_grid(grid_size)
        valve_register = ValveRegister()
        register_valves(valves,valve_register)
        self.nids2node = get_nid2nodes(grid_size,valve_register.nid2v)
    
    def test_center_node(self):
        nid = 4
        node = self.nids2node[nid]
        """Nodes"""
        self.assertEqual(node.get_node_neighbor_ids(),[3,5,1,7])
        """valves """
        vids = []
        for v in node.get_valve_neighbors():
            vids.append(v.vid)
            
        self.assertEqual(vids,[5,6,17,18])
        """pipes"""
        self.assertEqual(node.get_pipe_neighbor_ids(),[2,3,8,9])
        """degree"""
        self.assertEqual(node.degree(),4)
        # Closed pipes 
        self.assertEqual(node.closed_pipes,[False,False,False,False])
    
    def test_corner_node(self):
        nid = 0
        node = self.nids2node[nid]
        """Nodes"""
        self.assertEqual(node.get_node_neighbor_ids(),[None,1,None,3])
        """valves """
        vids = []
        for v in node.get_valve_neighbors():
            try:
                vids.append(v.vid)
            except:
                vids.append(None)
            
        self.assertEqual(vids,[None,0,None,12])
        """pipes"""
        self.assertEqual(node.get_pipe_neighbor_ids(),[None,0,None,6])
        """degree"""
        self.assertEqual(node.degree(),2)
        # Closed pipes 
        self.assertEqual(node.closed_pipes,[True,False,True,False])
   
        

if __name__ == '__main__':
    unittest.main()
        