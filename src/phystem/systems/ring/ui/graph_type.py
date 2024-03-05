from . import graph, graphs_cfg

def get_graph(cfg) -> type[graph.BaseGraph]:
    '''
    Retorna a classe do gráfico da simulação
    dado a sua configuração.
    '''
    cfg_to_cls = {
        graphs_cfg.MainGraphCfg: graph.MainGraph,
        graphs_cfg.SimpleGraphCfg: graph.SimpleGraph,
    }

    return cfg_to_cls[type(cfg)]