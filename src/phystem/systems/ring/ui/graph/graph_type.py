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