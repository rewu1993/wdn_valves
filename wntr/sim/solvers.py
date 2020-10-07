import numpy as np
import scipy.sparse as sp
import warnings
import logging
import scipy
import time

warnings.filterwarnings("error",'Matrix is exactly singular', sp.linalg.MatrixRankWarning)
np.set_printoptions(precision=3, threshold=10000, linewidth=300)

logger = logging.getLogger(__name__)


class NewtonSolver(object):
    """
    Newton Solver class.
    """
    
    def __init__(self, num_nodes, num_links, num_leaks, model, options=None):
        if options is None:
            options = {}
        self._options = options
        self.num_nodes = num_nodes
        self.num_links = num_links
        self.num_leaks = num_leaks
        self.model = model

        if 'MAXITER' not in self._options:
            self.maxiter = 3000
        else:
            self.maxiter = self._options['MAXITER']

        if 'TOL' not in self._options:
            self.tol = 1e-8
        else:
            self.tol = self._options['TOL']

        if 'BT_RHO' not in self._options:
            self.rho = 0.5
        else:
            self.rho = self._options['BT_RHO']

        if 'BT_MAXITER' not in self._options:
            self.bt_maxiter = 20
        else:
            self.bt_maxiter = self._options['BT_MAXITER']

        if 'BACKTRACKING' not in self._options:
            self.bt = True
        else:
            self.bt = self._options['BACKTRACKING']

        if 'BT_START_ITER' not in self._options:
            self.bt_start_iter = 0
        else:
            self.bt_start_iter = self._options['BT_START_ITER']
    def solve(self, Residual, Jacobian, x0):
        
        # print ("solve called")

        x = np.array(x0)

        use_r_ = False

        # MAIN NEWTON LOOP
        for outer_iter in range(10000):

            if use_r_:
                r = r_
                r_norm = new_norm
            else:
                r = Residual(x)
                r_norm = np.max(abs(r))

                print ("Iteration:")
                print (outer_iter)
                print ("Residual Norm:")
                print (np.linalg.norm(r),self.tol)

            if outer_iter<self.bt_start_iter:
               logger.debug('iter: {0:<4d} norm: {1:<10.2e}'.format(outer_iter, r_norm))

            if r_norm < self.tol:
                return [x, outer_iter, 1, 'Solved Successfully']

            J = Jacobian(x).tocsr()
            # print (J)



            if outer_iter<1:
                np.save("start_variables.npy",x)
                np.save("start_residuals.npy",r)
                print (np.max(abs(r)))
                print (np.max(abs(r)))
                sp.save_npz("start_jac.npz", J)
                print ("variable saved")
    
                

            # Call Linear solver
            try:
                d = -sp.linalg.spsolve(J,r,permc_spec='COLAMD',use_umfpack=False)
            except sp.linalg.MatrixRankWarning:
                return [x, outer_iter, 0, 'Jacobian is singular at iteration ' + str(outer_iter)]

            # Backtracking
            alpha = 1.0
            self.bt = False
            if self.bt and outer_iter>=self.bt_start_iter:
                use_r_ = True
                for iter_bt in range(self.bt_maxiter):
                    x_ = x + alpha*d
                    r_ = Residual(x_)
                    new_norm = np.max(abs(r_))
                    if new_norm < (1.0-0.0001*alpha)*r_norm:
                        x = x_
                        break
                    else:
                        alpha = alpha*self.rho

                if iter_bt+1 >= self.bt_maxiter:
                    return [x,outer_iter,0, 'Line search failed at iteration ' + str(outer_iter)]
                # logger.debug('iter: {0:<4d} norm: {1:<10.2e} alpha: {2:<10.2e}'.format(outer_iter, new_norm, alpha))
            else:
                # print ("no bt")
                x += d

        return [x, outer_iter, 0, 'Reached maximum number of iterations: ' + str(outer_iter)]


#     def solve(self, Residual, Jacobian, x0):

#         x = np.array(x0)

#         use_r_ = False

#         # MAIN NEWTON LOOP
#         for outer_iter in range(self.maxiter):


#             if use_r_:
#                 r = r_
#                 r_norm = new_norm
#             else:
#                 r = Residual(x)
#                 r_norm = np.max(abs(r))




#             # if outer_iter<self.bt_start_iter:
#             #    logger.debug('iter: {0:<4d} norm: {1:<10.2e}'.format(outer_iter, r_norm))
#             # print ("residual after solving",np.array(r))
#             if r_norm < self.tol:
#                 return [x, outer_iter, 1, 'Solved Successfully']

#             J = Jacobian(x).tocsr()
#             # print (J.todense())
            
#             r_ = Residual(x)




#             print ("Iteration:")
#             print (outer_iter)
#             if outer_iter<1:
#                 np.save("start_variables.npy",x)
#                 np.save("start_residual.npy",r_)
#                 sp.save_npz("start_jac.npz", J)
#                 print ("variable saved")
#             # print ("Residual Norm: ")
#             # print (r_norm)
#             # print ("Residual: ")
#             # print (r_)            
#             # print ("Variable: ")
#             # print (x)
#             # print ("Jabobian: ")
#             # print (J)
#             # Call Linear solver
#             try:
#                 d,_ = sp.linalg.gmres(J,r,tol=1e-8)
#             except sp.linalg.MatrixRankWarning:
#                 return [x, outer_iter, 0, 'Jacobian is singular at iteration ' + str(outer_iter)]
            
#             # print ("Difference: ")
#             # print (-d)
#             x -= d
            
#             new_norm = np.max(abs(r_))
            
            
#             # print ("Jabobian: ")
#             # print (J.todense().shape)
#             # for i,row in enumerate(J.todense()):
#             #     print ("row %d" %i)
#             #     print (row)
#             # print (x.dtype)
    

            
            
# #             # Backtracking
# #             alpha = 1.0
# #             if self.bt and outer_iter>=self.bt_start_iter:
# #                 use_r_ = True
# #                 for iter_bt in range(self.bt_maxiter):
# #                     x_ = x + alpha*d
# #                     r_ = Residual(x_)
# #                     new_norm = np.max(abs(r_))
# #                     if new_norm < (1.0-0.0001*alpha)*r_norm:
# #                         x = x_
# #                         break
# #                     else:
# #                         alpha = alpha*self.rho

# #                 if iter_bt+1 >= self.bt_maxiter:
# #                     return [x,outer_iter,0, 'Line search failed at iteration ' + str(outer_iter)]
# #                 # logger.debug('iter: {0:<4d} norm: {1:<10.2e} alpha: {2:<10.2e}'.format(outer_iter, new_norm, alpha))
# #             else:
# #                 x += d
            
#         return [x, outer_iter, 0, 'Reached maximum number of iterations: ' + str(outer_iter)]

     


