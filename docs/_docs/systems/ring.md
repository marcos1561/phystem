---
---

* This will become a table of contents (this text will be scrapped).
{:toc}

# Ring (Active rings)
At the present time, this is the most developed system. Its `Solver` is completely implemented with `C++` and loops are parallelized (in the CPU) when possible to improve performance. 

Two geometry types are implemented:

- Periodic Borders
- Stokes Geometry

There are 4 execution modes implemented:

- `RealTime`: Real-time rendering.
- `Collect`: Only data collection, without rendering.
- `Replay`: Saved data replay. Similar to `RealTime` but with saved data instead of on the fly data.
- `Video`: Video generation in real time or with saved data.

Many collectors and calculators have already been implemented:

1. Collectors:
    1. `CheckpointCol`: Generates a checkpoint that can be loaded by other simulations.
    2. `SnapshotsCol`: Periodically collect "simulation snapshots", that can be visualized by the `Replay` or `Video` execution mode.
    3. `DeltaCol`, `DenVelCol`, `CreationRateCol`: Collectors outside the scope of this text. See more details in their respective code documentation.
    4. `ColManager`: Manager for multiple collectors. Useful to run simulations with more than one data collector. 

2. Calculators: Each collector above, when applicable, has its respective calculator.

All collectors and calculators use the auto-save system in the core Phystem module, that is, a simulation can be stopped abruptly and resumed from the last saved point. 

# How to run a simulation?
To run a simulation, we need to instantiate the required configurations. In this section, a concrete example of a possible set of configurations will be provided, along with some comments about each one.

> ⚠️ 
>
> From this point on, it is assumed that the following import has been made: `from phystem.systems import ring`.

## System Dynamics Configuration
Controls elements such as force constants, particle diameter, etc. A possible choice is as follows:

```python
dynamic_cfg = ring.configs.RingCfg(
    num_particles=10,

    spring_k=8,
    spring_r=0.7,
    
    k_area=2,
    p0=3.545, # Circle
    
    k_invasion=10,

    diameter  = 1,
    max_dist  = 1 + 0.1666,
    rep_force = 12,
    adh_force = 0.75,
    
    relax_time=1,
    mobility=1,
    vo=1,
    
    trans_diff=0.1,
    rot_diff=1,
)
```

## Space Configuration
Settings for the physical space where the rings are located. The space is always a rectangle. Example:

```python
space_cfg = ring.configs.SpaceCfg(
    height=30,
    length=30,
)
```

## Initial State Configuration
Settings passed to the `Creator`, the object responsible for generating the initial configuration of the system. Currently, there is two types:

- `CreatorCfg`: Generates rings according to data passed by the user. It requires the initial positions of the rings' centers of mass and their self-propulsion directions. The following example generates 4 rings with 30 particles each, placing them around the origin with their self-propulsion directions pointing toward the origin:

    ```python
    from math import pi

    radius = dynamic_cfg.get_ring_radius() 
    k = 2

    creator_cfg = ring.configs.CreatorCfg(
        num_particles=dynamic_cfg.num_particles,
        num_rings=4,
        r=radius,
        angle=[pi/4, -3*pi/4, 3*pi/4, -pi/4],
        center=[
            [-k * radius, -k * radius], 
            [k * radius, k * radius], 
            [k * radius, -k * radius], 
            [-k * radius, k * radius], 
        ]
    )
    ```

    It is also possible to create an empty initial state (useful when working with stokes geometry.)

    ```python
    creator_cfg = ring.configs.CreatorCfg.empty()
    ```

- `RectangularGridCfg`: Generates rings in the vertices of a rectangular grid.

## Integration Configuration
These settings are related to the integration of the equations governing the system, such as $$ \Delta t $$. A space partitioning technique is used to optimize distance calculations, and its parameters are set here. Additionally, this is where you choose whether to use periodic boundaries or Stokes Geometry. Example:

```python
from phystem.systems.ring.run_config import IntegrationCfg, ParticleWindows, IntegrationType, InPolCheckerCfg, UpdateType

# Equilibrium ring radius
radius = dynamic_cfg.get_ring_radius()

# Dimensions of space partitioning at the level of particles.
num_cols, num_rows = space_cfg.particle_grid_shape(dynamic_cfg.max_dist)

int_cfg = IntegrationCfg(
    dt=0.01,
    particle_win_cfg=ParticleWindows(
        num_cols=num_cols, num_rows=num_rows,
        update_freq=1,
    ),
    integration_type=IntegrationType.euler,
    update_type=UpdateType.PERIODIC_WINDOWS,
)
```

This configuration is always passed to one of the execution mode configurations.

## Stokes Geometry Configuration
If Stokes flow (`update_type=UpdateType.STOKES`) is selected in the integration settings, you must provide the configuration for this geometry. Example: An obstacle centered at the origin with a radius equal to 1/5 of the channel height.

```python
# Equilibrium ring radius
radius = dynamic_cfg.get_ring_radius()

# Number of rings that fit in the channel
num_ring_in_rect = space_cfg.max_num_inside(2 * radius)

stokes_cfg = ring.configs.StokesCfg(
    obstacle_r  = space_cfg.height/5,
    obstacle_x  = 0,
    obstacle_y  = 0,
    create_length = radius * 2.01,
    remove_length = radius * 2.01,
    flux_force = 1, 
    obs_force = 15,
    num_max_rings = int(1.1 * num_ring_in_rect), 
)
```

## Execution Mode Configuration
Now all that's left is to choose the execution mode and run the simulation.

### RealTime
In this configuration, you can control the FPS, the number of steps the Solver executes per frame, etc. You can also customize what is being rendered by the `graph_cfg` argument.

```python
from phystem.systems.ring.ui.graph.graphs_cfg import SimpleGraphCfg

real_time_cfg = ring.run_config.RealTimeCfg(
    int_cfg=int_cfg,
    num_steps_frame=500,
    fps=30,
    graph_cfg=SimpleGraphCfg(
        show_circles=True,
    ),
)
```

### Video
Settings for saving a video. The main element you can control is the animation speed, which is influenced by the following parameters:

- speed: Ratio between simulation time and video time.
- tf: Final simulation time.
- duration: Video duration.

These three parameters are not independent, but this configuration accepts any combination of two (fixing the value of the third). Example: Generate a video called "video_test.mp4" from a simulation that runs until t=60:


```python
from phystem.systems.ring.ui.graphs_cfg import MainGraphCfg

save_cfg = ring.run_config.SaveCfg(
    int_cfg=int_cfg,
    path="./video_test.mp4",
    speed=3,
    tf=60,
    fps=30, 
    graph_cfg=SimpleGraphCfg(
        show_circles=True,
    ),
)
```

The last two execution modes (`Collect` and `Replay`) have their own sections.

## Running the Simulation
With all configurations created, you just need to instantiate the `Simulation` and execute it:

```python
sim = ring.Simulation(
    creator_cfg=creator_cfg, 
    dynamic_cfg=dynamic_cfg, 
    space_cfg=space_cfg, 
    run_cfg=run_cfg,
)

sim.run()
```
where run_cfg is one of the execution mode configurations.

If you are using Stokes geometry, the configuration should be passed as follows:

```python
sim = ring.Simulation(
    creator_cfg=creator_cfg, 
    dynamic_cfg=dynamic_cfg, 
    space_cfg=space_cfg, 
    run_cfg=run_cfg,
    other_cfgs={"stokes": stokes_cfg},
)
```

# How to Save, Load, and Share Simulations?
{: #saving_configs}
After creating a `Simulation` instance, all its configurations can be saved as follows:

```python
sim = ring.Simulation(**configs)
sim.save_configs("<path to my_configs>")
```
The configurations are saved in a [.yaml](https://yaml.org/spec/1.2.2/) file. This file can then be used to load a simulation:

```python
sim = ring.Simulation.load_from_configs("<path to some configs>")
sim.run()
```
Therefore, to share a simulation with someone, you only need to share the configuration file generated by the .save_configs() method.

If you need to modify the saved configurations before running, for example, to double the height of the space, you can do the following:

```python
configs = ring.run_config.load_configs("<path to configs>")
configs["space_cfg"].height *= 2 

sim = ring.Simulation(**configs)
sim.run()
```

# How to Collect Data?
To collect data, you need to use the `CollectCfg` execution configuration. Its main settings are:

- func: The function that performs the data collection procedure. Its signature is as follows:

    ```python
    def func_name(sim: ring.Simulation, cfg: Any) -> None
    ```
    This function is usually called the data collection pipeline.

- func_cfg: The configurations that are passed to func (the cfg parameter above).

> ℹ️
>
> One does not need to provide `func` if `func_cfg` is a `Collector` as explained in the section [Example: Using Collectors](#example-using-collectors).

## Exemple: Simple
Let's create a function that periodically collects the positions of the rings over time until the end of the simulation.

```python
import numpy as np
from pathlib import Path

from phystem.systems import ring
from phystem.systems.ring.run_config import CollectDataCfg

def collect_pipeline(sim: ring.Simulation, cfg):
    # Extracting objects of interest
    solver = sim.solver
    collect_cfg: CollectDataCfg = sim.run_cfg
    
    # Folder where the data will be saved
    save_path = collect_cfg.folder_path 

    count = 0
    collect_last_time = solver.time
    times = []
    while solver.time < collect_cfg.tf:
        solver.update()

        # Collect data every 'cfg["collect_dt"]' units of time
        if solver.time - collect_last_time > cfg["collect_dt"]:
            # IDs of active rings:
            # For periodic boundaries, this is unnecessary
            # and self.solver.rings_ids can be used directly.
            ring_ids = solver.rings_ids[:solver.num_active_rings]

            # Positions of the rings
            pos = np.array(solver.pos)[ring_ids]
            
            # Storing the collection time
            times.append(solver.time)

            # Saving the positions
            file_path = save_path / f"pos_{count}.npy"
            np.save(file_path, pos)
            
            count += 1
            collect_last_time = solver.time
    
    # Saving the collection times
    file_path = save_path / "times.npy"
    np.save(file_path, np.array(times))

    # Saving the simulation configurations
    sim.save_configs(save_path / "configs")
```
With the collection function created, the instantiation of `CollectDataCfg` is done as follows:

```python
collect_data_cfg = CollectDataCfg(
    int_cfg=int_cfg, # Configuration created earlier
    tf=10,
    folder_path="./data",
    func=collect_pipeline,
    func_cfg={"collect_dt": 1}, 
)
```

and running the simulation is as usual:

```python
sim = ring.Simulation(
    creator_cfg=creator_cfg, 
    dynamic_cfg=dynamic_cfg, 
    space_cfg=space_cfg, 
    run_cfg=collect_data_cfg,
)

sim.run()
```

## Example: Using Collectors
There is a collector that periodically collects the positions of the rings over time (more precisely, it collects the entire system state, which includes more than just the positions), called `SnapshotsCol`. So we can use it. With collectors, you only need to provide `func_cfg` with the respective collector configuration; it is not necessary to pass `func`:

```python
from phystem.systems.ring.collectors import SnapshotsCol, SnapshotsColCfg

collect_data_cfg = CollectDataCfg(
    int_cfg=int_cfg, # Configuration created earlier
    tf=10,
    folder_path="./data",
    func_cfg=SnapshotsColCfg(
        snaps_dt=1,
    ), 
)
```

Running the simulation with this configuration will yield the same result as the [Exemple: Simple](#exemple-simple), with the addition of some extra data.

> ℹ️
>
> `SnapshotsCol` will generate the following file structure:
>
>   
```
data
├── autosave
   ├── autosave
   ├── backup
├── data
├── config.yaml
```
> The data is in `data/data` and `config.yaml` contains the simulation configurations. Since we did not configure anything related to auto-saving, the `autosave` folder can be ignored in this case.

## How to Use Auto-Saves?
Simulations are generally time-consuming, so it is useful to create save points that can be restored in case of interruptions. Collectors have the `ColAutoSaveCfg` configuration, which, when provided, enables auto-saving. Let's use `SnapshotsCol` to demonstrate this system in action. The only modification needed to enable auto-saving in the [Example: Using Collectors](#example-using-collectors) is as follows:

```python
from phystem.systems import ring
from phystem.systems.ring.collectors import (
    SnapshotsCol, 
    SnapshotsColCfg, 
    ColAutoSaveCfg,
)

collect_data_cfg = ring.run_config.CollectDataCfg(
    int_cfg=int_cfg, # Configuration created earlier
    tf=10,
    folder_path="./data",
    func=SnapshotsCol.pipeline,
    func_cfg=SnapshotsColCfg(
        snaps_dt=1,
        autosave_cfg=ColAutoSaveCfg(
            freq_dt=3,
        ),
    ), 
)
```

In other words, we add the `ColAutoSaveCfg` configuration to `SnapshotsColCfg`, causing auto-saving to occur every 3 time units. The simulation can be run from the following file:

```python
# main.py
from phystem.systems import ring
from phystem.systems.ring.collectors import (
    SnapshotsCol, 
    SnapshotsColCfg, 
    ColAutoSaveCfg,
)

# Creating the configurations:
#   - creator_cfg 
#   - dynamic_cfg 
#   - space_cfg 
#   - int_cfg

collect_data_cfg = ring.run_config.CollectDataCfg(
    int_cfg=int_cfg, 
    tf=10,
    folder_path="./data",
    func=SnapshotsCol.pipeline,
    func_cfg=SnapshotsColCfg(
        snaps_dt=1,
        autosave_cfg=ColAutoSaveCfg(
            freq_dt=3,
        ),
    ), 
)

sim = ring.Simulation(
    creator_cfg=creator_cfg, 
    dynamic_cfg=dynamic_cfg, 
    space_cfg=space_cfg, 
    run_cfg=collect_data_cfg,
)
sim.run()
```

Run `main.py` and interrupt the execution with Ctrl-C before it finishes. To reload from the last saved point, simply add the checkpoint parameter to `CollectDataCfg`, passing an instance of `CheckpointCfg`, whose main argument is the folder where the auto-save is located, in our case `./data/autosave`. Therefore, `collect_data_cfg` should look like this:

```python
collect_data_cfg = CollectDataCfg(
    int_cfg=int_cfg, # Configuration created earlier
    tf=10,
    folder_path="./data",
    func=SnapshotsCol.pipeline,
    func_cfg=SnapshotsColCfg(
        snaps_dt=1,
        autosave_cfg=ColAutoSaveCfg(
            freq_dt=3,
        ),
    ), 
    checkpoint=ring.run_config.CheckpointCfg("./data/autosave"),
)
```
With this modification, running `main.py` again will resume execution from the last saved point.

Alternatively, you can load the last saved point in a new file:

```python
# load_autosave.py
from phystem.systems.ring import Simulation
from phystem.systems.ring.collectors import SnapshotsCol

configs = Simulation.configs_from_autosave("./data/autosave")
configs["run_cfg"].func = SnapshotsCol.pipeline

sim = Simulation(**configs) 
sim.run()
```

It is necessary to set `run_cfg` before running, as this configuration is not saved. `load_autosave.py` should be in the same folder as `main.py`.

## Example: Using Multiple Collectors in the Same Simulation
Suppose we want to collect arbitrary quantities Q1, Q2, and Q3 in a simulation. These quantities are completely independent. If we create a collector for each quantity, say `Q1Col`, `Q2Col`, and `Q3Col` (and their respective configurations), we could proceed by writing a data collection pipeline that uses them. However, since this is a relatively common task, there is a collector manager that automates this process. One way to configure such a multi-data collection simulation is:

```python
from phystem.systems.ring.collectors import ColManager, ColAutoSaveCfg

collect_data_cfg = CollectDataCfg(
    int_cfg=int_cfg, 
    tf=tf,
    folder_path="<path to datas directory>",
    func_cfg=ColManagerCfg(
        cols_cfgs={
            "q1": Q1ColCfg,
            "q2": Q2ColCfg,
            "q3": Q3ColCfg,
        },
        autosave_cfg=ColAutoSaveCfg(
            freq_dt=100,
            save_data_freq_dt=100,
        ),
    ),
)
```

Now, just run the simulation to start the data collection process. The advantages of this approach are:

- There is no need to manually write the data collection pipeline.
- `ColManager` takes care of auto-saving all collectors in a synchronized manner and saves the system state only once. If the pipeline were written manually, besides having to ensure that all collectors save at the same time, each collector would have its own copy of the system state in its auto-save, which is redundant.
