from . import graph, graphs_cfg

def get_graph_type(cfg: graphs_cfg.BaseGraphCfg | type[graphs_cfg.BaseGraphCfg]) -> type[graph.BaseGraph]:
    '''Retorna a classe do gráfico da simulação, dado a sua configuração.'''
    cfg_to_cls = {
        graphs_cfg.MainGraphCfg: graph.MainGraph,
        graphs_cfg.SimpleGraphCfg: graph.SimpleGraph,
        graphs_cfg.ReplayGraphCfg: graph.ReplayGraph,
    }

    if type(cfg) != type:
        cfg = type(cfg)

    return cfg_to_cls[cfg]