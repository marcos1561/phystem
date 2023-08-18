import example
import numpy as np

n = 10
vo = 0.1
size = 10

pos = size/2 * np.random.random((n, 2))

angle = np.random.random(n) * 2 * np.pi
vel = np.array([np.cos(angle), np.sin(angle)]).transpose()

solver = example.Solver(list(pos), list(vel), vo, 1, 1, 1, 1)
solver.update()

print(np.array(solver.pos).transpose().shape)