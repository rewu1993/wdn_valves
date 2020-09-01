from scripts.mesh import *
import unittest

class TestMesh(unittest.TestCase):
    
    def setUp(self):
        grid_size = 3
        self.mesh = Mesh(grid_size)
        
        
    def test_contraction(self):
        n1,n2 = self.mesh.nid2nodes[3],self.mesh.nid2nodes[6]
        identify_pairs_op = [[n1,n2,3]]
        self.mesh.perform_contractions(identify_pairs_op)
        print ("k dist after contraction", self.mesh.degree_distribution)
        print ("contraction reg", self.mesh.contraction_reg)
        self.assertEqual(len(self.mesh.degree_distribution[3]),4)
        self.assertEqual(len(self.mesh.degree_distribution[2]),3)
        
        # valves conditions on contracted nodes
        nid2v = self.mesh.valve_register.nid2v
        v1,v2 = nid2v[3][2],nid2v[6][1]
        self.assertTrue((v1.keep_open and v2.keep_open))
        self.assertTrue((v1.fail and v2.fail))
        
        # check valid pipes 
        self.assertEqual(len(self.mesh.valid_pids),11)
        
        
    def test_close_pipe_on_node(self):
        nid = 1
        pid2close = 8
        self.mesh.close_pipe_on_node(nid,pid2close)
        
        self.assertEqual(self.mesh.nid2nodes[1].closed_pipes, [False,False,True,True])
        self.assertEqual(self.mesh.nid2nodes[4].closed_pipes, [False,False,True,False])
        
        degree_dist = self.mesh.degree_distribution
        self.assertEqual(len(degree_dist[4]),0)
        self.assertEqual(len(degree_dist[3]),4)
        self.assertEqual(len(degree_dist[2]),5)
        print ("k dist after deletion ", self.mesh.degree_distribution)
        
        
    def test_reduce_degree(self):
        k = 4
        num = 0
        self.mesh.reduce_degree_num(k,num)
        degree_dist = self.mesh.degree_distribution
        closed_pids = self.mesh.closed_pids
        self.assertEqual(len(degree_dist[k]),num)
        self.assertEqual(len(closed_pids),1)
        print ("k dist after reduction ", self.mesh.degree_distribution)
        
        # check valid pipes 
        self.assertEqual(len(self.mesh.valid_pids),11)
        
    
        
if __name__ == '__main__':
    unittest.main()
