from . import graphs_cfg
from . import graphs

def get_graph_type(cfg: type[graphs_cfg.BaseGraphCfg]) -> type[graphs.BaseGraph]:
    '''Retorna a classe do gráfico da simulação, dado a sua configuração.'''
    cfg_to_cls = {
        graphs_cfg.SimpleGraphCfg: graphs.MainGraph,
        graphs_cfg.ReplayGraphCfg: graphs.ReplayGraph,
    }

    if type(cfg) != type:
        cfg = type(cfg)

    return cfg_to_cls[cfg]


def get_ring_colors(cfg, solver):
    ring_cfg_to_cls = {
        graphs_cfg.RandomColorsCfg: graphs.RandomColor,
        graphs_cfg.VelocityColorsCfg: graphs.VelocityColor,
        graphs_cfg.AsphericityColorsCfg: graphs.AsphericityColor,
    }
    if type(cfg) is str:
        for Cfg_i in ring_cfg_to_cls.keys():
            if cfg == Cfg_i.name:
                cfg = Cfg_i()
                break
        else:
            valid_name = [c.name for c in ring_cfg_to_cls.keys()]
            raise Exception(f"RingColorCfg name `{cfg}` in not valid. Valid names: {valid_name}")
    
    return ring_cfg_to_cls[type(cfg)](cfg, solver)