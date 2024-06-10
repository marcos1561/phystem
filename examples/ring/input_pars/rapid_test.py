import numpy as np
import time

# a = np.random.random((15000, 15, 2))
# np.save("test.npy", a)

start = time.time()
for _ in range(1000):
    np.load("test.npy")
final = time.time()

print(final - start)
