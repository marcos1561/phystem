from multiprocessing import Pool
import time 


def time_it(func, n):
    t1 = time.time()
    func(n)
    t2 = time.time()
    return t2 - t1

# if __name__ == '__main__':
def f(x):
    sum = 0
    for i in range(1, 100000):
        sum += 1/i**2
    return x

def sequencial(n):
    r = []
    for i in range(n):
        r.append(f((i, 2*i)))
    print(r)

def parallel(n):
    args = [(i, 2*i) for i in range(n)]

    with Pool() as p:
        r = p.map(f, args)
    print(r)

n = 10
# print("seq:", time_it(sequencial, n))
# print("par:", time_it(parallel, n))

def func(*a):
    print(a)

func(1, 2)
