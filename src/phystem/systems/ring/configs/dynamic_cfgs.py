import math
from phystem.systems.ring import utils

class RingCfg:
    "Variáveis relacionadas a dinâmica do sistema."

    def __init__(self,  spring_k: float, spring_r: float, mobility: float, 
        relax_time: float, vo: float, trans_diff: float, rot_diff: float, 
        diameter: float, max_dist: float, rep_force: float, adh_force: float, 
        num_particles: int, k_invasion: float | str="auto",
        area_potencial="target_area", p0: float=None, p0_format: float=None, 
        area0: float=None, k_format: float=None, k_area: float=None) -> None:
        '''
        Variáveis relacionadas a dinâmica do sistema de anéis.

        Parâmetros:
        -----------
        spring_k:
            Constante das molas que conectam partículas vizinhas no mesmo anel.
        
        spring_r:
            Comprimento de equilíbrio das molas que conectam partículas vizinhas no mesmo anel.

        mobility:
            Constate que multiplica a força resultante na equação de movimento da velocidade.
        
        relax_time:
            Tempo de relaxamento da polarização em direção a velocidade do anel.
        
        vo:
            Rapidez da velocidade auto-propulsora.
        
        trans_diff:
            Ruído translacional.
        
        rot_diff:
            Ruído rotacional.

        diameter:
            Diâmetro efetivo das partículas (Distância em que a a força partícula-partícula é nula).
        
        max_dist:
            Distância máxima de interação entre as partículas.
        
        rep_force:
            Constante da força de repulsão entre as partículas.
        
        adh_force: 
            Constante da força de atração entre as partículas.
        
        k_invasion:
            Valor do módulo da força anti-invasões. O padrão é "auto", que seta automaticamente
            esse parâmetro para o menor valor possível capaz de desfazer invasões.
        
        area_potencial: str
            Tipo de potencial a ser utilizada na área dos anéis. O único que faz sentido é "target_area",
            os outros apenas estão ai por experimentação.

        p0:
            Flexibilidade da membrana dos anéis. Se for `None`, o parâmetro `area0`
            deve ser informado.

        area0:
            Área alvo dos anéis. Essa área é relativa a área do polígono formado 
            pelos centros das partículas do anel (a área das partículas não é considerada).
            Se for `None`, o parâmetro `p0` deve ser informado.
        
        k_area:
            Constante da força da área.
        '''
        valid_potentials = ["target_area", "target_area_and_format", "format", "target_perimeter"]
        if area_potencial not in valid_potentials:
            raise ValueError(f"Potencial '{area_potencial}' não válido. Os valores permitidos são {valid_potentials}")

        if p0 is None and area0 is None:
            raise Exception("Ao menos um dos parâmetros 'p0' e 'area0' devem ser setados.")

        has_format = area_potencial in ["format", "target_area_and_format"]
        has_target_area = area_potencial in ["target_area", "target_area_and_format"]

        if has_format:
            if k_format is None:
                raise ValueError(f"'k_format' deve ser especificado para o potencial '{area_potencial}'.")
            if p0_format is None:
                raise ValueError(f"'p0_format' deve ser especificado para o potencial '{area_potencial}'.")
        
        if has_target_area and k_area is None:
            raise ValueError("'k_area' deve ser especificado para o potencial.")

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
        self._p0 = value
        self._area0 = self.get_area0(self.num_particles)

    @property
    def area0(self):
        return self._area0
    
    @area0.setter
    def area0(self, value):
        self._area0 = value
        self._p0 = self.get_p0(self.num_particles)

    @property
    def num_particles(self):
        return self._num_particles

    def change_num_particles(self, value: int, fix="p0"):
        '''
        Muda o número de partículas setado. É possível escolher
        qual quantidade fica fixa com o parâmetro `fix`, cujos
        possíveis valores são: ["p0", "area0"]
        '''
        fix_names = ["p0", "area0"]
        if fix not in ["p0", "area0"]:
            raise ValueError(f"fix deve ser um dos valores em {fix_names}")

        self._num_particles = value
        if fix == "p0":
            self.area0 = self.get_area0(self.num_particles)
        else:
            self.p0 = self.get_p0(self.num_particles)

    def get_equilibrium_relative_area(self):
        '''
        Área de equilíbrio do anel relativa a `area0`. Essa área
        é apenas a área do polígono formado pelos centros das partículas do anel.
        '''
        return utils.equilibrium_relative_area(
            k_a=self.k_area, k_m=self.spring_k, a0=self.area0,
            spring_r=self.spring_r, num_particles=self.num_particles,
        )
    
    def get_equilibrium_area(self, consider_particles=True):
        '''
        Área de equilíbrio do anel.
        
        Parâmetros:
        ----------
        consider_particles:
            Se for `True`, leva em consideração a área das partículas do anel,
            caso contrário, a área retornada é a área do polígono formado pelos
            centros das partículas do anel.
        '''
        area_add = 0
        if consider_particles:
            area_add = self.get_particles_area()

        return self.get_equilibrium_relative_area() * self.area0 + area_add

    def get_max_k_adh(self, dt, relative_area, x=1):
        '''
        Retorna o valor máximo de `k_adh` em relação a problemas numéricos. `x` deve
        ser um valor entre 0 e 1, que será utilizado para definir em qual ponto da região de
        adesão (que será `x * adh_size`) é feito o cálculo.
        '''
        area0 = self.area0
        adh_size = self.max_dist - self.diameter
        return utils.max_k_adh(adh_size, dt, self.k_area, area0, self.spring_r, relative_area,
            self.mobility, self.vo, x)

    def get_min_inv_force(self):
        '''
        Valor mínimo da força de anti-invasão para ganhar da força
        de repulsão entra as partículas no pior dos casos.
        '''
        theta = math.acos((1/2 * self.spring_r / self.diameter)**(1/3)) 
        return self.spring_k * (2 * math.sin(theta) - self.spring_r/self.diameter * math.tan(theta))

    def get_area0(self, num_particles):
        '''
        Retorna a área de equilíbrio da força da área para
        o dado número de partículas, levando em consideração `p0`.
        '''
        return (num_particles * self.spring_r / self.p0)**2
    
    def get_p0(self, num_particles):
        '''
        Retorna o p0 para o dado número de partículas, levando em 
        consideração `area0`.
        '''
        return num_particles * self.spring_r / self.area0**.5
    
    def get_ring_radius(self):
        return utils.ring_radius(
            self.diameter, self.k_area, self.spring_k,
            self.area0, self.spring_r, self.num_particles,
        )
    
    def get_particles_area(self):
        "Contribuição das partículas na área dos anéis."
        return utils.particles_area(
            self.num_particles, self.spring_r, self.diameter,
        )
    
    def ring_spawn_pos(self):
        '''
        Posições de um anel centrado em x=(0, 0) com área igual
        a sua área de equilíbrio no formato de um polígono regular.

        Retorno:
        --------
        pos: ndarray com shape (num_particles, 2)
            Posições das partículas do anel.
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

