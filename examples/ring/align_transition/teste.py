
class MyCLass:
    def __init__(self) -> None:
        self.a = [1, 2]
        self.b = [3, 4]
        self.c = []


with open("state.pickle", "rb") as f:
    a = pickle.load(f)["my_obj"]
    print(a.a)
    print(a.b)
    print(a.c)


# with open("state.pickle", "wb") as f:
#     pickle.dump({"my_obj": MyCLass()}, f)