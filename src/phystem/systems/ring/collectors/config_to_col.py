from phystem.systems.ring.collectors.base import RingCol, ColCfg

class Configs2Collector:
    configs_to_collector: dict[type[ColCfg], type[RingCol]] = {}

    @staticmethod
    def add(ConfigT: type[ColCfg], CollectorT: type[RingCol]):
        if ConfigT in Configs2Collector.configs_to_collector.keys():
            return

        Configs2Collector.configs_to_collector[ConfigT] = CollectorT

    def get(ConfigT: type[ColCfg]):
        return Configs2Collector.configs_to_collector[ConfigT]