from enum import Enum, auto
from tkinter import W, S, E, N
from tkinter import ttk

class ControlWidget:
    def __init__(self, parent: ttk.Frame) -> None:
        self.parent = parent
        pass

    def grid(self):
        pass

class CbOption(ControlWidget):
    def __init__(self, parent: ttk.Frame, num_cols=3) -> None:
        super().__init__(parent)
        self.names = []
        self.variables = []
        self.callbacks = []
        self.num_cols = num_cols

    def add(self, name, variable, callback):
        self.names.append(name)
        self.variables.append(variable)
        self.callbacks.append(callback)

    def grid(self):
        n = len(self.names)
        for i in range(n):
            col = i % (self.num_cols)
            row = i // (self.num_cols)

            cb = ttk.Checkbutton(self.parent, command=self.callbacks[i],
            text=self.names[i], variable=self.variables[i])

            cb.grid(row=row, column=col, sticky=W, padx=5)

class PlayButton(ttk.Button):
    class State(Enum):
        running = auto()
        stopped = auto()

    def __init__(self, parent: ttk.Frame, callback, init_state: State, 
        running_text="Running", stopped_text="Stopped", *args, **kwargs):
        super().__init__(parent, command=self.on_click, *args, **kwargs)

        self.state_text = {
            PlayButton.State.running: running_text,
            PlayButton.State.stopped: stopped_text,
        }
        self.next_state = {
            PlayButton.State.running: PlayButton.State.stopped,
            PlayButton.State.stopped: PlayButton.State.running,
        }
        self.callback = callback
        self.bttn_state = init_state
        self.configure({"text": self.state_text[self.bttn_state]})

    def on_click(self):
        self.bttn_state = self.next_state[self.bttn_state]
        self.configure({"text": self.state_text[self.bttn_state]})
        self.callback()

if __name__ == "__main__":
    import tkinter as tk
    root = tk.Tk()
    bttn = PlayButton(root, callback=lambda : print("Noice"),  width=20)

    bttn.grid(pady=10, padx=10)
    root.mainloop()