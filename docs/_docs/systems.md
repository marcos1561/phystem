---
---

## How to use the physical systems already implemented with phystem?

The sub-package `phystem.systems` contains the physical systems already implemented with phystem.

In general, to use them, you need to create an instance of `Simulation`, which is located in the `simulation.py` module of the respective system, and run the `run` method. `Simulation` requires the following configurations:

1. `creator_cfg`: Settings for creating the initial configuration of the system.
2. `dynamic_cfg`: Settings for the system's dynamics.
3. `space_cfg`: Settings for the physical space where the system is located.
4. `run_cfg`: Settings for the execution mode.

Items 1, 2, and 3 are located in the `configs.py` module of the respective system, so you can check this file to understand how to instantiate these configurations.

Item 4 can be found in two locations:

1. If the system uses the default execution settings, they are located in `phystem.core.run_config`.
2. If the system has extended these settings, they are located in the `run_config.py` module of the respective system.

> ⚠️
>
> 1. If you are using a system that relies on the C++ module (ring and szabo), you need to compile the code that generates this module. 
For more information, refer to [Compiling the C++ Module]({{ "docs/installation.html#installation_compilation" | relative_url }}).

Currently, the following systems are implemented:

### [Ring]({{ "docs/systems/ring.html" | relative_url }})
Implementation of multiple active rings, with some minor modifications, as presented by Teixeira et al. [[1]](#1).

<!-- ![]({{ "assets/images/rings.gif" | relative_url }}) -->
<img src="{{ 'assets/images/rings.gif' | relative_url }}" alt width="700"/>
### Szabo
Implementation of the active particle model proposed by Szabó et al. [[2]](#2).

<!-- ![]({{ "assets/images/szabo.gif" | relative_url }}) -->
<img src="{{ 'assets/images/szabo.gif' | relative_url }}" alt width="700"/>

### Vicsek
Implementation of the model proposed by Vicsek et al. [[3]](#3). 
> ⚠️
> 
> The implementation is incomplete and currently contains only a highly disorganized version of its solver.

### Random Walker
System implemented in the tutorial [How to use phystem?]({{ 'docs/tutorial_step_by_step.html' | relative_url }}).

## Referências
<a id="1">[1]</a> 
TEIXEIRA, E. F.; FERNANDES, H. C. M.; BRUNNET, L. G. A single active ring model with velocity self-alignment. Soft Matter, v. 17, n. 24, p. 5991–6000, 23 jun. 2021. 

<a id="2">[2]</a>
SZABÓ, B. et al. Phase transition in the collective migration of tissue cells: experiment and model. Physical Review. E, Statistical, Nonlinear, and Soft Matter Physics, v. 74, n. 6 Pt 1, p. 061908, dez. 2006.

<a id="3">[3]</a>
VICSEK, T. et al. Novel type of phase transition in a system of self-driven particles. Physical Review Letters, v. 75, n. 6, p. 1226–1229, 7 ago. 1995. 