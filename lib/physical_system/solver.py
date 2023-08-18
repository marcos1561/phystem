import numpy as np
from math import atan2

from physical_system.configs import SelfPropellingCfg
import physical_system.cpp_lib as cpp_lib

class CppSolver:
    def __init__(self, pos: np.ndarray, vel: np.ndarray, self_prop_cfg: SelfPropellingCfg, 
        size: float, dt: float, rng_seed=None) -> None:
        pos = cpp_lib.PosVec(pos.T)
        vel = cpp_lib.PosVec(vel.T)

        self_prop_cfg = cpp_lib.SelfPropellingCfg(self_prop_cfg.cpp_constructor_args())

        if rng_seed is None:
            rng_seed = -1

        self.cpp_solver = cpp_lib.Solver(pos, vel, self_prop_cfg, size, dt, 10, rng_seed)
        self.time = 0
        self.dt = dt

    @property
    def n(self):
        return self.cpp_solver.n;

    @property
    def pos(self):
        return self.cpp_solver.py_pos
    
    @property
    def vel(self):
        return self.cpp_solver.py_vel
    
    @property
    def propelling_vel(self):
        return self.cpp_solver.py_propelling_vel
    
    @property
    def propelling_angle(self):
        return self.cpp_solver.propelling_angle
    
    @property
    def random_number(self):
        return self.cpp_solver.random_number

    def mean_vel_vec(self):
        return self.cpp_solver.mean_vel_vec()

    def update(self):
        # self.cpp_solver.update1()
        # self.cpp_solver.update2()
        # self.cpp_solver.update_arr()
        # self.cpp_solver.update_self_propelling()
        self.cpp_solver.update_self_propelling_windows()
        self.time += self.dt

    def mean_vel(self):
        return self.cpp_solver.mean_vel()

class VicsekSolver:
    def __init__(self, pos: np.ndarray, vel: np.ndarray, vo:float, ro: float, nabla: float, 
        alpha: float, box_size: float, potencial_cfg, dt: float) -> None:
        self.pos = pos
        self.vel = vel
        self.ro = ro
        self.vo = vo
        self.nabla = nabla
        self.alpha = alpha
        self.box_size = box_size

        self.potencial_cfg = potencial_cfg

        self.time = 0
        self.dt = dt
        self.n = self.pos.shape[1]

        self.pos_super = np.array([self.pos]*self.pos.shape[1])
        self.pos_super_2 = self.pos.T.reshape(self.pos.shape[1], 2, 1)

        self.sum_neighbors_vel_matrix = np.zeros((2, self.n), dtype=np.float64)
        
        self.neighbors_matrix = np.zeros((self.n, self.n), dtype=np.bool8)
        self.dist_matrix = np.zeros((self.n, self.n), dtype=np.float64)
        self.unit_r_matrix = np.zeros((self.n, 2, self.n), dtype=np.float64)
        self.sum_force_matrix = np.zeros((2, self.n), dtype=np.float64)
        
        self.critical_angle = np.zeros(self.n, dtype=np.float64)
        self.is_critical_dist = np.zeros(self.n, dtype=np.bool8)

    def mean_vel(self):
        return np.linalg.norm(self.vel.sum(axis=1))/(self.n * self.vo)
    
    def calc_sum_neighbors_vel_matrix(self):
        # sum_neighbors_vel_matrix = np.zeros((2, self.n), dtype=np.float64)
        
        # distance_matrix = np.zeros((self.n, self.n), dtype=np.float64)
        # neighbors_matrix = np.full((self.n, self.n), False, dtype=np.bool8)
        # np.fill_diagonal(neighbors_matrix, True)

        # for i in range(self.n-1):
        #     diff = (self.pos[:, i+1:] - self.pos[:, i].reshape(2, 1))**2
        #     dist = np.sqrt(diff[0] + diff[1])

        #     distance_matrix[i][i+1:] = dist
        #     neighbors_matrix[i][i+1:] = dist < self.ro
        
        # distance_matrix += distance_matrix.transpose()
        # neighbors_matrix += neighbors_matrix.transpose()
        
        # for id, neighbors in enumerate(neighbors_matrix):
        #     sum_vel = self.vel[:, neighbors].sum(axis=1)
        #     sum_neighbors_vel_matrix[:, id] = sum_vel
        

        for i in range(self.n):
            diff = self.pos - self.pos[:, i].reshape(2, 1)
            
            diff_square = diff**2
            dist = np.sqrt(diff_square[0] + diff_square[1])
            
            is_close = dist < self.ro

            active = self.vel[:, is_close].sum(axis=1)
            self.sum_neighbors_vel_matrix[:, i] = active


            # self.dist_matrix[i] = dist 
            # self.neighbors_matrix[i] = is_close 

            # dist[dist==0] = 1e-5
            # self.unit_r_matrix[i] = -diff/dist

        # diff_matrix = self.pos_super - self.pos_super_2
        # distance_matrix = diff_matrix**2
        # distance_matrix = np.sqrt(distance_matrix.sum(axis=1))
        # neighbors_matrix = distance_matrix < self.ro
        # self.sum_neighbors_vel_matrix = self.vel.dot(neighbors_matrix.T)


        # neighbors_matrix = np.full((self.n, self.n), False, dtype=np.bool8)
        # for particle_id in range(self.n):
        #     particle_pos = self.pos[:,particle_id]
        #     for other_id in range(particle_id+1, self.n):
        #         other_pos = self.pos[:, other_id]
                
        #         dx = particle_pos[0] - other_pos[0]
        #         dy = particle_pos[1] - other_pos[1]
        #         dist = (dx**2 + dy**2)**.5

        #         neighbors_matrix[particle_id, other_id] = dist < self.ro
        # neighbors_matrix += neighbors_matrix.T
        # np.fill_diagonal(neighbors_matrix, True)
        # sum_neighbors_vel_matrix = self.vel.dot(neighbors_matrix.T)

        # return sum_neighbors_vel_matrix

        return

    def calc_interactve_force_matrix(self):
        # critical_dist = self.dist_matrix < self.potencial_cfg.rc
        # close_ra = self.dist_matrix < self.potencial_cfg.ra

        # for id in range(self.n):
        #     critical_dist_ids = np.where(critical_dist[id] == True)[0]
        #     if critical_dist_ids.size > 0:
        #         self.is_critical_dist[id] = True
            
        #         x_force, y_force = -self.unit_r_matrix[id][:, critical_dist_ids[0]]
        #         if x_force == 0:
        #             x_force = 1e-5

        #         self.critical_angle[id] =  np.arctan2(y_force, x_force)
            
        #     self.is_critical_dist[id] = False

        #     coeff = self.neighbors_matrix[id]

        #     is_mid_dist = close_ra[id] & np.logical_not(critical_dist[id])
        #     coeff[is_mid_dist] = 1/4 * (self.dist_matrix[id][is_mid_dist] - self.potencial_cfg.re)/(self.potencial_cfg.ra - self.potencial_cfg.re)

        #     self.sum_force_matrix[:, id] = self.unit_r_matrix[id].dot(coeff)

        for particle_i in range(self.n):
            force = np.zeros(2, dtype=np.float64)
            self.is_critical_dist[particle_i] = False
            for other_i, dist_i in enumerate(self.dist_matrix[particle_i]):
                if particle_i == other_i:
                    continue
                if dist_i > self.ro:
                    continue

                r_vec = self.pos[:, other_i] - self.pos[:, particle_i] 

                if dist_i < self.potencial_cfg.rc:
                    self.is_critical_dist[particle_i] = True
                
                    if r_vec[0] == 0:
                        r_vec[0] = 1e-5
                    self.critical_angle[particle_i] =  atan2(-r_vec[1], -r_vec[0])
                    break

                r_vec = r_vec / np.linalg.norm(r_vec)

                if dist_i < self.potencial_cfg.ra:
                    force += 1/4 * (dist_i - self.potencial_cfg.re) * r_vec / (self.potencial_cfg.ra - self.potencial_cfg.re)  
                else:
                    force += r_vec
            
            self.sum_force_matrix[:, particle_i] = force

    def update(self):
        self.calc_sum_neighbors_vel_matrix()
        # self.calc_interactve_force_matrix()

        ### New angle - Vicssek        
        self.sum_neighbors_vel_matrix[0][self.sum_neighbors_vel_matrix[0] == 0] = 1e-5
        alignment_angle = np.arctan2(self.sum_neighbors_vel_matrix[1], self.sum_neighbors_vel_matrix[0])
        
        # random_angle = np.pi * (np.random.random(self.n) * 2 - 1)
        random_angle = 1/2 * (np.random.random(self.n) * 2 - 1)
        
        d_theta = self.alpha * alignment_angle + random_angle * self.nabla
        ####

        ### Potencial force
        # total_sum = self.alpha * self.sum_neighbors_vel_matrix + self.potencial_cfg.strength * self.sum_force_matrix
        # total_sum[0, total_sum[0] == 0] = 1e-5
        
        # random_angle = 1/2 * (np.random.random(self.n) * 2 - 1)
        # d_theta = np.arctan2(total_sum[1], total_sum[0]) + self.nabla * random_angle
        # d_theta[self.is_critical_dist] = self.critical_angle[self.is_critical_dist]
        ###

        ### Update vel and pos
        self.vel[:] = np.array([np.cos(d_theta), np.sin(d_theta)]) * self.vo

        # x, y = self.vel[0].copy(), self.vel[1].copy()
        # cos, sen = np.cos(d_theta), np.sin(d_theta)
        # self.vel[0] = x * cos - y * sen
        # self.vel[1] = x * sen + y * cos

        self.pos[:] = self.pos + self.dt * self.vel

        ### Periodic borders
        box_size = self.box_size/2
        self.pos[0][self.pos[0] > box_size] = -box_size
        self.pos[0][self.pos[0] < -box_size] = box_size
        self.pos[1][self.pos[1] > box_size] = -box_size
        self.pos[1][self.pos[1] < -box_size] = box_size

        self.time += self.dt
