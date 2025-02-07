from phystem.core.autosave import AutoSavable

class AAutoSaveCfg:
    def __init__(self, freq) -> None:
        self.freq = freq

class A(AutoSavable):
    def __init__(self, root_dir, autosave_cfg: AAutoSaveCfg = None, load_autosave=False) -> None:
        super().__init__(root_dir)
        self.num_autosaves = 0
        self.var1 = None
        self.var2 = None

        self.autosave_cfg = autosave_cfg

        if load_autosave:
            self.load_autosave()

    @property
    def vars_to_save(self):
        return [
            "var1",
            "var2",
            "num_autosaves",
        ]
    
    def do_something(self):
        for i in range(10):
            self.var1 = i
            self.var2 = i +1
            self.check_autosave(i)

    def check_autosave(self, i):
        if i % self.autosave_cfg.freq == 0:
            self.num_autosaves += 1
            self.exec_autosave()

a = A("root_dir", AAutoSaveCfg(freq=2))
result = a.var1, a.var2, a.num_autosaves
expected = None, None, 0
print(result == expected)
a.do_something()

print("===")

a = A("root_dir", AAutoSaveCfg(freq=2), load_autosave=True)
result = a.var1, a.var2, a.num_autosaves
expected = 8, 9, 5
print("r:", result)
print("e:", expected)
print(result == expected)