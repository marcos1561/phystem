from phystem.cpp_lib.data_types import PosVec, PyVecList, PyVecList3d, Vector3d, List2d

class Ring:
    def __init__(self, pos0, self_prop_angle0, dynamic_cfg, 
        size, dt, num_col_windows, seed=-1, num_skip_steps=0, integration_type=0) -> None: ...

    pos: Vector3d = ...
    self_prop_angle = ...
    
    pos_continuos: Vector3d = ...

    pos_t: PyVecList3d = ...
    graph_points: Vector3d = ...
    
    spring_forces: Vector3d = ...
    vol_forces: Vector3d = ...
    area_forces: Vector3d = ...
    total_forces: Vector3d = ...
    
    differences: Vector3d = ...

    num_rings: int = ...
    num_particles: int = ...
    num_time_steps: int = ...

    def update_normal() -> None: ...
    def update_windows() -> None: ...

class SelfPropelling:
    def __init__(self, pos0, vel0, propelling_cfg, size, dt, num_windows, seed=-1) -> None: ...

    n: int = ...
    pos: PosVec = ...
    vel: PosVec = ...
    propelling_vel: PosVec = ...
    propelling_angle= ...
    py_pos: PyVecList = ...
    
    py_pos: PosVec = ...
    py_vel: PosVec = ...
    py_propelling_vel: PosVec = ...

    random_number: float = ...

    def update_normal() -> None: ...
    def update_windows() -> None: ...
    def mean_vel() -> float: ...
    def mean_vel_vec() -> list: ...