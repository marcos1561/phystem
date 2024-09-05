import copy
from phystem.systems.ring.configs import RingCfg

class ExtremeConfigs:
    def __init__(self, base_dynamic: RingCfg) -> None:
        self.base_dynamic = base_dynamic
        self.configs = {}
        self.extremes = {
            "align": {},
            "den": {},
            "force": {},
        }
        self.extras = {}

    def get_key(self, align, den, force):
        return align, den, force

    def add_extreme(self, name, dynamic_cfg=None, stokes_cfg=None):
        if dynamic_cfg is None:
            dynamic_cfg = {}
        if stokes_cfg is None:
            stokes_cfg = {}

        self.extremes[name][1] = [dynamic_cfg.get("high", {}), stokes_cfg.get("high", {})]
        self.extremes[name][0] = [dynamic_cfg.get("low", {}), stokes_cfg.get("low", {})]

    def add_extra(self, align, den, force, dynamic_cfg=None, stokes_cfg=None):
        if dynamic_cfg is None:
            dynamic_cfg = {}
        if stokes_cfg is None:
            stokes_cfg = {}

        key = self.get_key(align, den, force)
        extras = {}
        extras["dynamic"] = dynamic_cfg
        extras["stokes"] = stokes_cfg
        self.extras[key] = extras

    def get(self, align, den, force):
        key = self.get_key(align, den, force)
        return self.configs[key]

    def add(self, align, den, force, dynamic_cfg, stokes_cfg):
        key = self.get_key(align, den, force)
        
        dynamic_cfg_copy = copy.deepcopy(self.base_dynamic)
        for name, value in dynamic_cfg.items():
            dynamic_cfg_copy.__setattr__(name, value)
        
        self.configs[key] = [dynamic_cfg_copy, stokes_cfg]

    def save(self, path, align, den, force):
        import yaml
        with open(path, "w") as f:
            yaml.dump(self.get(align, den, force), f)

    def generate(self):
        from itertools import product
        keys = list(product([0, 1], repeat=3))  
        for align, den, force in keys:
            is_extreme_high = {"align": align, "den": den, "force": force}
            key = self.get_key(align, den, force)
            if key in self.configs.keys():
                continue

            # has_conflict = False
            # dynamic_all_keys = []
            # for extremes_cfgs in self.extremes.values():
            #     dynamic_all_keys.extend(list(extremes_cfgs["dynamic_cfg"].keys()))

            dynamic_cfg = {}
            stokes_cfg = {}
            for extreme_name, extremes_cfgs in self.extremes.items():
                is_high = is_extreme_high[extreme_name]

                current_dynamic_cfg, current_stokes_cfg = extremes_cfgs[is_high]
                extra_cfgs = self.extras.get(key, {})

                dynamic_cfg.update(current_dynamic_cfg)
                dynamic_cfg.update(extra_cfgs.get("dynamic", {}))

                stokes_cfg.update(current_stokes_cfg)
                stokes_cfg.update(extra_cfgs.get("stokes", {}))
            
            self.add(align, den, force, dynamic_cfg, stokes_cfg)

extreme_configs = ExtremeConfigs(
    base_dynamic = RingCfg(
        spring_k=23,
        spring_r=0.7,
        
        area_potencial="target_area",
        k_area=4,
        p0=4,

        k_invasion = 11,
        
        diameter  = 1,
        max_dist  = 1 * (1 + 0.1818),
        # max_dist  = 1 + 0.5*0.1,
        rep_force = 23,
        adh_force = 1,
        
        relax_time=50,
        mobility=1,
        vo=0.5,
        
        trans_diff=0,
        rot_diff=1/3,
    ),
)


extreme_configs.add_extreme(
    name = "align",
    dynamic_cfg = {
        "high": {"relax_time": 1},
        "low": {"relax_time": 50},
    }
)

extreme_configs.add_extreme(
    name = "den",
    stokes_cfg = {
        "high": {"flux_force": 5},
        "low": {"flux_force": 0.5},
    }
)

extreme_configs.add_extreme(
    name = "force",
    dynamic_cfg = {
        "high": {"adh_force": 10},
        "low": {"adh_force": 1},
    }
)

extreme_configs.add_extra(1, 1, 1, 
    dynamic_cfg = {
        "spring_k": 28,
        "rep_force": 28,
    },
    stokes_cfg = {
        "obs_force": 28,
    },
)

# extreme_configs.add(
#     align=1, den=1, force=0,
#     dynamic_cfg = {
#         "adh_force": 3.3,
#         "relax_time": 2,
#     },
#     stokes_cfg = {"flux_force": 2.12},
# )

extreme_configs.generate()

# import yaml

# with open("teste2.yaml", "w") as f:
#     yaml.dump(extreme_configs.get(align=1, den=1, force=0), f)
