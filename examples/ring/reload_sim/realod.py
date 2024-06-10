'''
Carrega uma simulação a partir de um arquivo de configuração
'''
from phystem.systems import ring

sim = ring.Simulation.load_from_configs("config_real_time")
sim.run()