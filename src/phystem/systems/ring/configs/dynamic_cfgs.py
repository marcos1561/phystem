import math
from phystem.systems.ring import utils

class RingCfg:
    "Variáveis relacionadas a dinâmica do sistema."

    def __init__(self,  spring_k: float, spring_r: float, mobility: float, 
        relax_time: float, vo: float, trans_diff: float, rot_diff: float, 
        diameter: float, max_dist: float, rep_force: float, adh_force: float, 
        num_particles: int, k_invasion: float="auto",
        area_potencial="target_area", p0: float=None, p0_format: float=None, 
        area0: float=None, k_format: float=None, k_area: float=None) -> None:
        '''
        Variables related to the dynamics of the ring system.

        Parameters:
        -----------
        spring_k:
            Spring constant connecting neighboring particles in the same ring.
        
        spring_r:
            Equilibrium length of the springs connecting neighboring particles in the same ring.

        mobility:
            Constant that multiplies the resultant force in the velocity equation of motion.
        
        relax_time:
            Relaxation time of the polarization towards the ring velocity.
        
        vo:
            Magnitude of the self-propulsion velocity.
        
        trans_diff:
            Translational noise.
        
        rot_diff:
            Rotational noise.

        diameter:
            Effective diameter of the particles (distance at which the particle-particle force is zero).
        
        max_dist:
            Maximum interaction distance between particles.
        
        rep_force:
            Constant of the repulsive force between particles.
        
        adh_force: 
            Constant of the attractive force between particles.
        
        k_invasion:
            Magnitude of the anti-invasion force. Default is "auto", which automatically sets
            this parameter to the minimum value capable of undoing invasions.
        
        area_potencial: str
            Type of potential to be used for the ring area. The only meaningful value is "target_area",
            others are included for experimentation.

        p0:
            Flexibility of the ring membrane. If `None`, the parameter `area0`
            must be provided.

        area0:
            Target area of the rings. This area is relative to the area of the polygon formed 
            by the centers of the ring particles (the area of the particles themselves is not considered).
            If `None`, the parameter `p0` must be provided.
        
        k_area:
            Constant of the area force.
        '''
        valid_potentials = ["target_area", "target_area_and_format", "format", "target_perimeter"]
        if area_potencial not in valid_potentials:
            raise ValueError(f"Potential '{area_potencial}' not  valid. Valid values are: {valid_potentials}")

        if p0 is None and area0 is None:
            raise Exception("At least one of the parameters 'p0' and 'area0' should be specified.")

        has_format = area_potencial in ["format", "target_area_and_format"]
        has_target_area = area_potencial in ["target_area", "target_area_and_format"]

        if has_format:
            if k_format is None:
                raise ValueError(f"'k_format' must be specified for the potential '{area_potencial}'.")
            if p0_format is None:
                raise ValueError(f"'p0_format' must be specified for the potential '{area_potencial}'.")
        
        if has_target_area and k_area is None:
            raise ValueError("'k_area' must be specified for the potential.")

        if area_potencial == "format":
            area0 = -1
            p0 = -1
            k_area = -1
        if not has_format:
            k_format = -1
            p0_format = -1

        self._num_particles = num_particles

        self.spring_k = spring_k
        self.spring_r = spring_r
        
        if p0 is None:
            self.area0 = area0
        else:
            self.p0 = p0

        self.area_potencial = area_potencial
        self.k_area = k_area
        self.k_format = k_format
        self.p0_format = p0_format

        self.mobility = mobility
        self.relax_time = relax_time
        self.vo = vo

        self.trans_diff = trans_diff
        self.rot_diff = rot_diff

        self.diameter = diameter
        self.max_dist = max_dist
        self.rep_force = rep_force
        self.adh_force = adh_force
        
        if k_invasion == "auto":
            self.k_invasion = self.get_min_inv_force()
        else:
            self.k_invasion = k_invasion

    @property
    def p0(self):
        return self._p0
    
    @p0.setter
    def p0(self, value):
        self._p0 = float(value)
        self._area0 = self.get_area0(self.num_particles)

    @property
    def area0(self):
        return self._area0
    
    @area0.setter
    def area0(self, value):
        self._area0 = float(value)
        self._p0 = self.get_p0(self.num_particles)

    @property
    def num_particles(self):
        return self._num_particles

    @property
    def peclet(self):
        '''
        Péclet number (Pe) of the system. High Pe means advection is
        more relevant than diffusion and low Pe means the contrary. 
        '''
        tau_advection = self.get_ring_radius() / self.vo
        tau_diffusion = 1 / self.rot_diff
        return tau_diffusion / tau_advection

    def change_num_particles(self, value: int, fix="p0"):
        '''
        Changes the set number of particles. You can choose which quantity remains fixed with the `fix` parameter,
        whose possible values are: ["p0", "area0"]
        '''
        fix_names = ["p0", "area0"]
        if fix not in ["p0", "area0"]:
            raise ValueError(f"fix must be one of the values in {fix_names}")

        self._num_particles = value
        if fix == "p0":
            self.area0 = self.get_area0(self.num_particles)
        else:
            self.p0 = self.get_p0(self.num_particles)

    def get_equilibrium_relative_area(self):
        '''
        Equilibrium area of the ring relative to `area0`. This area
        is only the area of the polygon formed by the centers of the ring particles.
        '''
        return utils.equilibrium_relative_area(
            k_a=self.k_area, k_m=self.spring_k, a0=self.area0,
            spring_r=self.spring_r, num_particles=self.num_particles,
        )
    
    def get_equilibrium_area(self, consider_particles=True):
        '''
        Equilibrium area of the ring.

        Parameters:
        ----------
        consider_particles:
            If `True`, takes into account the area of the ring particles,
            otherwise, the returned area is the area of the polygon formed by
            the centers of the ring particles.
        '''
        area_add = 0
        if consider_particles:
            area_add = self.get_particles_area()

        return self.get_equilibrium_relative_area() * self.area0 + area_add

    def get_max_k_adh(self, dt, relative_area, x=1):
        '''
        Returns the maximum value of `k_adh` with respect to numerical issues. `x` should
        be a value between 0 and 1, which will be used to define at which point in the adhesion region
        (which will be `x * adh_size`) the calculation is performed.
        '''
        area0 = self.area0
        adh_size = self.max_dist - self.diameter
        return utils.max_k_adh(adh_size, dt, self.k_area, area0, self.spring_r, relative_area,
            self.mobility, self.vo, x)

    def get_min_inv_force(self):
        '''
        Minimum value of the anti-invasion force required to overcome the repulsive force
        between particles in the worst-case scenario.
        '''
        theta = math.acos((1/2 * self.spring_r / self.diameter)**(1/3)) 
        return self.spring_k * (2 * math.sin(theta) - self.spring_r/self.diameter * math.tan(theta))

    def get_area0(self, num_particles):
        '''
        Returns the equilibrium area of the area force for
        the given number of particles, taking into account `p0`.
        '''
        return (num_particles * self.spring_r / self.p0)**2
    
    def get_p0(self, num_particles):
        '''
        Returns p0 for the given number of particles, taking into 
        account `area0`.
        '''
        return num_particles * self.spring_r / self.area0**.5
    
    def get_ring_radius(self):
        return utils.ring_radius(
            self.diameter, self.k_area, self.spring_k,
            self.area0, self.spring_r, self.num_particles,
        )
    
    def get_particles_area(self):
        "Contribution of the particles to the area of the rings."
        return utils.particles_area(
            self.num_particles, self.spring_r, self.diameter,
        )
    
    def ring_spawn_pos(self):
        '''
        Positions of a ring centered at x=(0, 0) with area equal
        to its equilibrium area in the shape of a regular polygon.

        Returns:
        --------
        pos: ndarray with shape (num_particles, 2)
            Positions of the ring particles.
        '''
        return utils.ring_spawn_pos(
            self.k_area, self.spring_k, self.area0, 
            self.spring_r, self.num_particles,
        )

    def will_invade(self, relative_area, tol=1e-3):
        area0 = self.area0
        _, est_value = utils.invasion_equilibrium_config(
            k_r=self.rep_force, k_m=self.spring_k, k_a=self.k_area,
            lo=self.spring_r, ro=self.diameter, area0=area0,
            relative_area_eq=relative_area, vo=self.vo, mu=self.mobility,
        )
        return abs(est_value[0]) + abs(est_value[1]) > tol

    def cpp_constructor_args(self):
        return {
            "spring_k": self.spring_k,
            "spring_r": self.spring_r,
            "k_area": self.k_area,
            "k_format": self.k_format,
            "area_potencial": self.area_potencial,
            "p0": self.p0,
            "p0_format": self.p0_format,
            "area0": self.area0,
            "k_invasion": self.k_invasion,
            "mobility": self.mobility,
            "relax_time": self.relax_time,
            "vo": self.vo,
            "trans_diff": self.trans_diff,
            "rot_diff": self.rot_diff,
            "diameter": self.diameter,
            "max_dist": self.max_dist,
            "rep_force": self.rep_force,
            "adh_force": self.adh_force,
        }

    def info(self):
        return (
            f"k_mola = {self.spring_k:.2f}\n"
            f"k_area = {self.k_area:.2f} | k_format = {self.k_format:.2f}\n"
            f"p_0 = {self.p0:.2f} | area0 = {self.area0:.2f}\n"
            f"\n"
            f"D_T = {self.trans_diff:.2f}\n"
            f"D_R = {self.rot_diff:.2f}\n"
            f"\n"
        )

