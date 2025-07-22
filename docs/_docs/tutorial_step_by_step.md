---
---

## How to use Phystem?
To demonstrate its usage, we will implement a single random walker. The requirements for our system are as follows:

- Walking behavior: Constant speed with the velocity direction varying randomly, with controllable variation intensity.  
- System space: Square region with periodic boundaries.
- Initial configuration: Place the walker in a random position within the space, with a random velocity direction.

Each Phystem system has a base class that provides its skeleton. To implement it, we need to inherit from this base class. 
> ⚠️ 
>
> 1. If you haven't installed Phystem yet, please refer to the [installation instructions]({{ "docs/installation.html" | relative_url }}).
> 2. In code blocks, the first comment contains the name of the file where the code should be placed.

### 0. File Organization

For organizational purposes, each system will be placed in separate files. By the end of this tutorial, the file structure should look like this:

```
random_walker
├── creator.py
├── solver.py
├── configs.py
├── simulation.py
└── main.py
```
### 1. Initial Configuration
The `Creator` must implement the `create` method, which should return the initial configuration data. Therefore, we need to decide how the data representing the system's configuration is structured. In this case, we will choose to represent the position and velocity as a list, and the structure of the system's configuration will simply be another list containing the position and velocity.

``` python
# creator.py

import random
from math import pi, cos, sin

from phystem.core.creators import CreatorCore

class Creator(CreatorCore):
    def __init__(self, speed: float,  size: int, rng_seed: int = None) -> None:
        super().__init__(rng_seed)
        self.speed = speed # Walker speed.
        self.size = size # Size of the system's space side.

    def create(self):
        # Initial position
        x = self.size/2 * (random.random() * 2 - 1)
        y = self.size/2 * (random.random() * 2 - 1)
        self.pos = [x, y]

        # Initial velocity
        angle = 2* pi * random.random()
        self.vel = [self.speed * cos(angle), self.speed * sin(angle)]

        config = [self.pos, self.vel]
        return config
```
### 2. Solver
Next, let's implement the component responsible for evolving our walker over time, the `Solver`. It must implement the `update` method, which performs the execution of a time step.

``` python
# solver.py

import random
from math import pi, cos, sin

from phystem.core.solvers import SolverCore

class Solver(SolverCore):
    def __init__(self, pos0: list[float], vel0: list[float], 
        noise_strength: float, size: int, dt: float) -> None:
        super().__init__()
        self.size = size

        # Initial system configuration
        self.pos = pos0
        self.vel = vel0
        
        self.noise_strength = noise_strength

        # Time step size
        self.dt = dt

        # Simulation time
        self.time = 0

    def update(self) -> None:
        # Position update
        self.pos[0] += self.dt * self.vel[0]
        self.pos[1] += self.dt * self.vel[1]
        
        # Velocity update: Rotate by the angle d_angle
        d_angle = self.noise_strength * pi * (random.random() * 2 - 1)
        new_vx = cos(d_angle) * self.vel[0] + sin(d_angle) * self.vel[1]
        new_vy = -sin(d_angle) * self.vel[0] + cos(d_angle) * self.vel[1]
        
        self.vel[0] = new_vx
        self.vel[1] = new_vy

        # Periodic boarders
        for i in range(2):
            if self.pos[i] > self.size/2:
                self.pos[i] = -self.size/2
            elif self.pos[i] < -self.size/2:
                self.pos[i] = self.size/2

        self.time += self.dt
```

> ℹ️
>
> If you are implementing a physical system that requires high computational power, implementing the solver purely in Python might not be the best choice. One possible solution is to build the solver in a high-performance language and call it from the Python solver. One way to achieve this is by using [pybind11](https://pybind11.readthedocs.io/en/stable/index.html#), a library that allows creating Python modules that call code written in C++. 
### 3. Configurations
Typically, there are various configurations used to explore a physical system, so to facilitate their management, Phystem expects them to be encapsulated in classes. By default, a simulation application expects to receive four types of configurations:

1. System dynamics configurations.
2. Configurations for the physical space where the system resides.
3. Configurations used by the `Creator`.
4. Execution configurations.

Item 4 has a default implementation that will suffice for the purposes of this system. The other items require implementation. For organizational purposes, their classes will be implemented in a separate file.

``` python
# configs.py

class DynamicCfg:
    def __init__(self, vo: float, noise_strength: float):
        '''
        Parameters:
            vo: 
                Walker speed.
            
            noise_strength: 
                Walker noise strength.
        '''
        self.vo = vo
        self.noise_strength = noise_strength
    
class CreatorCfg:
    def __init__(self, speed: float,  size: int) -> None:
        '''
        Parameters:
            speed: 
                Speed used to create the velocity.
            
            size: 
                Space side length.
        '''
        self.speed = speed
        self.size = size
    
class SpaceCfg:
    def __init__(self, size: float) -> None:
        '''
        Parameters:
            size: 
                Space side length.
        '''
        self.size = size
```

> ℹ️
>
> For small simulations, writing configurations in this way may seem like an unnecessary overhead. However, it simplifies organization and management as the number of configurations increases. In particular, this format facilitates storing the configurations used in a completed simulation (Phystem stores configurations using .yaml files).

### 4. Simulation Application

Now we just need to implement the system that actually runs the simulation. There are different execution modes:

1. Real-time rendering
2. Data collection
3. Data replay
4. Video generation

Each mode requires the user to work a bit to implement it. We will focus only on item 1. The base class for a simulation application is `SimulationCore`, which requires the methods `get_solver` and `get_creator` to be implemented. These methods are responsible for returning instances of the `Solver` and `Creator` that will be used in the simulation.

``` python
# simulation.py

from phystem.core.simulation import SimulationCore

from creator import Creator 
from solver import Solver 
from configs import SpaceCfg, CreatorCfg, DynamicCfg

class Simulation(SimulationCore): 
    # These lines are not necessary; they only inform the variable types, 
    # which is useful for code completion to work well.
    dynamic_cfg: DynamicCfg
    creator_cfg: CreatorCfg
    space_cfg: SpaceCfg
    solver: Solver

    def get_creator(self):
        return Creator(
            speed=self.creator_cfg.speed,
            size=self.creator_cfg.size,
        )
            
    def get_solver(self):
        po0, vel0 = self.creator.create()

        return Solver(
            po0, vel0,
            noise_strength = self.dynamic_cfg.noise_strength,
            size = self.space_cfg.size,
            dt = self.run_cfg.int_cfg.dt,
        )
```

Since we want real-time rendering, we also need to implement the `run_real_time` method, which is responsible for configuring how the physical system is visualized.

The system rendering is done using `matplotlib`, so the first task is to create a `matplotlib` figure and the appropriate `Axes`. We'll simply show the particle moving, so a single `Axes` will suffice. These objects should be created as follows:

``` python
# simulation.py

fig = plt.Figure()
ax = fig.add_subplot()
```

> ⚠️ 
>
> **Do not** use `fig, ax = plt.subplots()` as it conflicts with tkinter (the tool used to create the UI).

Phystem already provides a graph for rendering particles on a plane, which can be used as follows:

``` python
# simulation.py

from phystem.gui_phystem.mpl import graph

particles_graph = graph.ParticlesGraph(
    ax=ax, 
    pos=self.solver.pos, 
    space_size=self.space_cfg.size,
)
```

Additionally, we need to create the function that generates the frames. In this function, the `Solver` needs to execute time steps, and the graph needs to be updated.

``` python
# simulation.py

def update(frame):
    self.solver.update()
    particles_graph.update()
```
> ℹ️
>
> It is often desirable to perform more than one time step per frame, which can be easily achieved by calling `solver.update` in a loop. The default class for real-time execution configuration has the member `num_steps_frame`, which should be used for this purpose.

Finally, we need to run the application that will contain the animation, information, and controls, which can be customized according to the user's preferences. This is simply done by calling the `run_app` method, passing the created figure and the function that generates the frames.

``` python
# simulation.py

self.run_app(fig, update)
```

The complete implementation of `Simulation` is:

``` python
# simulation.py

import matplotlib.pyplot as plt

from phystem.core.simulation import SimulationCore
from phystem.core.run_config import RealTimeCfg
from phystem.gui_phystem.mpl import graph

from creator import Creator 
from solver import Solver 
from configs import *

class Simulation(SimulationCore): 
    dynamic_cfg: DynamicCfg
    creator_cfg: CreatorCfg
    space_cfg: SpaceCfg
    solver: Solver

    def get_creator(self):
        return Creator(
            speed=self.creator_cfg.speed,
            size=self.creator_cfg.size,
        )
            
    def get_solver(self):
        po0, vel0 = self.creator.create()

        return Solver(
            po0, vel0,
            noise_strength = self.dynamic_cfg.noise_strength,
            size = self.space_cfg.size,
            dt = self.run_cfg.dt,
        )

    def run_real_time(self):
        fig = plt.Figure()
        ax = fig.add_subplot()
        
        particle_graph = graph.ParticlesGraph(
            ax=ax, 
            pos=self.solver.pos, 
            space_size=self.space_cfg.size,
        )

        def update(frame):
            self.solver.update()
            particle_graph.update()

        self.run_app(fig, update)
```
### 5. How to Run the Simulation?
To run the simulation, we need to create an instance of the simulation and call the `run` method. The instantiation of `Simulation` requires passing the configurations. In addition to those implemented in step 3, it is also necessary to provide the execution configuration for the real-time rendering mode. An example of a possible configuration for a simulation is as follows:

``` python
# main.py

from phystem.core.run_config import RealTimeCfg, IntegrationCfg

from configs import *
from simulation import Simulation

dynamic_cfg = DynamicCfg(
    vo=1,
    noise_strength= 0.1,
)

space_cfg = SpaceCfg(
    size=10,
)

creator_cfg = CreatorCfg(
    speed=dynamic_cfg.vo,
    size=space_cfg.size,
)

run_cfg = RealTimeCfg(
    IntegrationCfg(
        dt=0.1,
    ),
    num_steps_frame=1,
    fps=60,
)

sim = Simulation(creator_cfg, dynamic_cfg, space_cfg, run_cfg)
sim.run()
```

If this file is executed, a window will appear with an animation similar to this:

![]({{ "assets/images/random_walk.gif" | relative_url}})

We could continue with our implementation by adding many other features. Some options are:

1. Measure the execution time of the time steps and display it in the GUI.
2. By default, there are some buttons in the generated GUI, but their functionalities need to be implemented.
3. Set up a data collection pipeline for analysis.
4. Expand the walker graph to render extra auxiliary items for debugging the application, such as an arrow indicating the walker's velocity.
5. Add multiple walkers (perhaps introducing interaction dynamics between walkers).

The possibilities are endless! While this tutorial ends here, I hope it’s shed some light and will guide you as you explore and build your own physical systems.

Thank you for reading!